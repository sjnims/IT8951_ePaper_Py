"""SPI interface abstraction for IT8951 communication."""

import sys
import time
from abc import ABC, abstractmethod
from typing import Protocol

from IT8951_ePaper_Py.constants import GPIOPin, SPIConstants
from IT8951_ePaper_Py.exceptions import CommunicationError, InitializationError


class GPIOInterface(Protocol):
    """Protocol for GPIO operations."""

    BCM: int
    OUT: int
    IN: int

    def setmode(self, mode: int) -> None:
        """Set the GPIO pin numbering mode."""
        ...

    def setup(
        self, channel: int | list[int], direction: int, pull_up_down: int = 20, initial: int = -1
    ) -> None:
        """Set up a GPIO pin."""
        ...

    def output(self, channel: int | list[int], state: int | bool | list[int] | list[bool]) -> None:
        """Set GPIO pin output value."""
        ...

    def input(self, channel: int) -> int:
        """Read GPIO pin input value."""
        ...

    def cleanup(self) -> None:
        """Clean up GPIO resources."""
        ...


class SPIDeviceInterface(Protocol):
    """Protocol for SPI device operations."""

    max_speed_hz: int
    mode: int

    def open(self, bus: int, device: int) -> None:
        """Open SPI device."""
        ...

    def writebytes(self, values: list[int]) -> None:
        """Write bytes to SPI."""
        ...

    def xfer2(
        self, values: list[int], speed_hz: int = 0, delay_usecs: int = 0, bits_per_word: int = 0
    ) -> list[int]:
        """Transfer data to/from SPI."""
        ...

    def close(self) -> None:
        """Close SPI device."""
        ...


class SPIInterface(ABC):
    """Abstract base class for SPI communication."""

    @abstractmethod
    def init(self) -> None:
        """Initialize SPI interface."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close SPI interface and cleanup resources."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Hardware reset the device."""
        pass

    @abstractmethod
    def wait_busy(self, timeout_ms: int = 5000) -> None:
        """Wait for device to be ready."""
        pass

    @abstractmethod
    def write_command(self, command: int) -> None:
        """Write a command to the device."""
        pass

    @abstractmethod
    def write_data(self, data: int) -> None:
        """Write data to the device."""
        pass

    @abstractmethod
    def write_data_bulk(self, data: list[int]) -> None:
        """Write bulk data to the device."""
        pass

    @abstractmethod
    def read_data(self) -> int:
        """Read data from the device."""
        pass

    @abstractmethod
    def read_data_bulk(self, length: int) -> list[int]:
        """Read bulk data from the device."""
        pass


class RaspberryPiSPI(SPIInterface):
    """SPI interface implementation for Raspberry Pi."""

    def __init__(self) -> None:
        """Initialize Raspberry Pi SPI interface."""
        self._gpio: GPIOInterface | None = None
        self._spi: SPIDeviceInterface | None = None
        self._initialized = False

    def init(self) -> None:
        """Initialize SPI interface."""
        if self._initialized:
            return

        try:
            import spidev  # pyright: ignore[reportMissingModuleSource]
            from RPi import GPIO  # pyright: ignore[reportMissingModuleSource]

            self._gpio = GPIO  # type: ignore[assignment]
            self._gpio.setmode(GPIO.BCM)
            self._gpio.setup(GPIOPin.RESET, GPIO.OUT)
            self._gpio.setup(GPIOPin.BUSY, GPIO.IN)

            self._spi = spidev.SpiDev()  # type: ignore[assignment]
            self._spi.open(0, 0)
            self._spi.max_speed_hz = SPIConstants.SPI_SPEED_HZ
            self._spi.mode = SPIConstants.SPI_MODE

            self._initialized = True
            self.reset()

        except ImportError as e:
            raise InitializationError(
                f"Failed to import required modules for Raspberry Pi: {e}"
            ) from e
        except Exception as e:
            raise InitializationError(f"Failed to initialize SPI: {e}") from e

    def close(self) -> None:
        """Close SPI interface and cleanup resources."""
        if self._spi:
            self._spi.close()
            self._spi = None

        if self._gpio:
            self._gpio.cleanup()
            self._gpio = None

        self._initialized = False

    def reset(self) -> None:
        """Hardware reset the device."""
        if not self._gpio:
            raise InitializationError("GPIO not initialized")

        self._gpio.output(GPIOPin.RESET, 0)
        time.sleep(0.1)
        self._gpio.output(GPIOPin.RESET, 1)
        time.sleep(0.1)

    def wait_busy(self, timeout_ms: int = 5000) -> None:
        """Wait for device to be ready."""
        if not self._gpio:
            raise InitializationError("GPIO not initialized")

        start_time = time.time()
        while time.time() - start_time < timeout_ms / 1000:
            if self._gpio.input(GPIOPin.BUSY) == 0:
                return
            time.sleep(0.001)

        raise CommunicationError(f"Device busy timeout after {timeout_ms}ms")

    def write_command(self, command: int) -> None:
        """Write a command to the device."""
        if not self._spi:
            raise InitializationError("SPI not initialized")

        self.wait_busy()
        preamble = SPIConstants.PREAMBLE_CMD
        self._spi.writebytes([preamble >> 8, preamble & 0xFF])
        self._spi.writebytes([command >> 8, command & 0xFF])

    def write_data(self, data: int) -> None:
        """Write data to the device."""
        if not self._spi:
            raise InitializationError("SPI not initialized")

        self.wait_busy()
        preamble = SPIConstants.PREAMBLE_DATA
        self._spi.writebytes([preamble >> 8, preamble & 0xFF])
        self._spi.writebytes([data >> 8, data & 0xFF])

    def write_data_bulk(self, data: list[int]) -> None:
        """Write bulk data to the device."""
        if not self._spi:
            raise InitializationError("SPI not initialized")

        self.wait_busy()
        preamble = SPIConstants.PREAMBLE_DATA
        self._spi.writebytes([preamble >> 8, preamble & 0xFF])

        for value in data:
            self._spi.writebytes([value >> 8, value & 0xFF])

    def read_data(self) -> int:
        """Read data from the device."""
        if not self._spi:
            raise InitializationError("SPI not initialized")

        self.wait_busy()
        preamble = SPIConstants.PREAMBLE_READ
        self._spi.writebytes([preamble >> 8, preamble & 0xFF])

        dummy = SPIConstants.DUMMY_DATA
        self._spi.writebytes([dummy >> 8, dummy & 0xFF])

        result = self._spi.xfer2([0x00, 0x00])
        return (result[0] << 8) | result[1]

    def read_data_bulk(self, length: int) -> list[int]:
        """Read bulk data from the device."""
        if not self._spi:
            raise InitializationError("SPI not initialized")

        self.wait_busy()
        preamble = SPIConstants.PREAMBLE_READ
        self._spi.writebytes([preamble >> 8, preamble & 0xFF])

        dummy = SPIConstants.DUMMY_DATA
        self._spi.writebytes([dummy >> 8, dummy & 0xFF])

        data: list[int] = []
        for _ in range(length):
            result = self._spi.xfer2([0x00, 0x00])
            data.append((result[0] << 8) | result[1])

        return data


class MockSPI(SPIInterface):
    """Mock SPI interface for testing and development on non-Pi systems."""

    def __init__(self) -> None:
        """Initialize mock SPI interface."""
        self._initialized = False
        self._busy = False
        self._last_command: int | None = None
        self._data_buffer: list[int] = []
        self._read_data: list[int] = []

    def init(self) -> None:
        """Initialize mock SPI interface."""
        if self._initialized:
            return

        self._initialized = True
        self.reset()

    def close(self) -> None:
        """Close mock SPI interface."""
        self._initialized = False
        self._busy = False
        self._last_command = None
        self._data_buffer.clear()
        self._read_data.clear()

    def reset(self) -> None:
        """Simulate hardware reset."""
        self._busy = False
        time.sleep(0.1)

    def wait_busy(self, timeout_ms: int = 5000) -> None:
        """Simulate waiting for device ready."""
        if self._busy:
            time.sleep(0.01)
            self._busy = False

    def write_command(self, command: int) -> None:
        """Simulate writing a command."""
        if not self._initialized:
            raise InitializationError("Mock SPI not initialized")

        self.wait_busy()
        self._last_command = command
        self._busy = True

    def write_data(self, data: int) -> None:
        """Simulate writing data."""
        if not self._initialized:
            raise InitializationError("Mock SPI not initialized")

        self.wait_busy()
        self._data_buffer.append(data)

    def write_data_bulk(self, data: list[int]) -> None:
        """Simulate writing bulk data."""
        if not self._initialized:
            raise InitializationError("Mock SPI not initialized")

        self.wait_busy()
        self._data_buffer.extend(data)

    def read_data(self) -> int:
        """Simulate reading data."""
        if not self._initialized:
            raise InitializationError("Mock SPI not initialized")

        self.wait_busy()
        if self._read_data:
            return self._read_data.pop(0)
        return 0xFFFF

    def read_data_bulk(self, length: int) -> list[int]:
        """Simulate reading bulk data."""
        if not self._initialized:
            raise InitializationError("Mock SPI not initialized")

        self.wait_busy()
        data: list[int] = []
        for _ in range(length):
            if self._read_data:
                data.append(self._read_data.pop(0))
            else:
                data.append(0xFFFF)
        return data

    def set_read_data(self, data: list[int]) -> None:
        """Set data to be returned by read operations (for testing)."""
        self._read_data.extend(data)

    def get_last_command(self) -> int | None:
        """Get the last command written (for testing)."""
        return self._last_command

    def get_data_buffer(self) -> list[int]:
        """Get the data buffer (for testing)."""
        return self._data_buffer.copy()


def create_spi_interface() -> SPIInterface:
    """Create appropriate SPI interface based on platform."""
    if sys.platform == "linux" and ("arm" in sys.platform or "aarch" in sys.platform):
        return RaspberryPiSPI()
    return MockSPI()
