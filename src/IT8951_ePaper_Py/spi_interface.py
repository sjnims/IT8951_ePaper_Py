"""SPI interface abstraction for IT8951 communication.

This module provides hardware abstraction for SPI communication with the IT8951
e-paper controller. It includes:

- Protocol definitions for GPIO and SPI operations
- Abstract base class for SPI interfaces
- MockSPI implementation for testing
- RaspberryPiSPI implementation for hardware
- Factory function for automatic interface selection

Examples:
    Creating an SPI interface::

        # Automatic selection based on platform
        spi = create_spi_interface()

        # Or explicitly use mock for testing
        spi = MockSPI()

        # Initialize and use
        spi.init()
        spi.write_command(0x01)
        data = spi.read_data()
        spi.close()
"""

import sys
import time
from abc import ABC, abstractmethod
from typing import Protocol

from IT8951_ePaper_Py.constants import GPIOPin, ProtocolConstants, SPIConstants, TimingConstants
from IT8951_ePaper_Py.exceptions import CommunicationError, InitializationError, IT8951TimeoutError


def _get_pi_revision() -> str | None:
    """Read Raspberry Pi revision from /proc/cpuinfo.

    Returns:
        str | None: Revision string or None if not found.
    """
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("Revision"):
                    return line.split(":")[-1].strip()
    except OSError:
        # File doesn't exist or can't be read (not on Pi)
        return None
    return None


def _detect_from_new_revision(revision: str) -> int | None:
    """Detect Pi version from new-style revision codes.

    Args:
        revision: Revision string (6+ hex digits).

    Returns:
        int | None: Pi version or None if not detected.
    """
    if len(revision) < 6:
        return None

    try:
        # Extract processor field (bits 12-15, chars 2-3 in hex string)
        processor = int(revision[-4:-2], 16) if len(revision) > 4 else 0
        # Map processor to Pi version
        # BCM2835=0 (Pi1/Zero), BCM2836=1 (Pi2), BCM2837=2 (Pi3), BCM2711=3 (Pi4), BCM2712=4 (Pi5)
        processor_map = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}
        return processor_map.get(processor)
    except ValueError:
        return None


def _detect_from_old_revision(revision: str) -> int | None:
    """Detect Pi version from old-style revision codes.

    Args:
        revision: Revision string.

    Returns:
        int | None: Pi version or None if not detected.
    """
    old_style_map = {
        # Pi 1
        (
            "0002",
            "0003",
            "0004",
            "0005",
            "0006",
            "0007",
            "0008",
            "0009",
            "000d",
            "000e",
            "000f",
            "0010",
            "0011",
            "0012",
            "0013",
            "0014",
            "0015",
        ): 1,
        # Pi 2
        ("a01040", "a01041", "a21041", "a22042"): 2,
        # Pi 3
        ("a02082", "a22082", "a32082", "a52082", "a22083"): 3,
    }

    for revisions, version in old_style_map.items():
        if revision in revisions:
            return version
    return None


def _detect_from_prefix(revision: str) -> int | None:
    """Detect Pi version from revision prefix.

    Args:
        revision: Revision string.

    Returns:
        int | None: Pi version or None if not detected.
    """
    prefix_map = {
        # Pi 4 prefixes
        ("a03", "b03", "c03", "d03"): 4,
        # Pi 5 prefixes
        ("c04", "d04"): 5,
    }

    for prefixes, version in prefix_map.items():
        if any(revision.startswith(prefix) for prefix in prefixes):
            return version
    return None


def detect_raspberry_pi_version() -> int:
    """Detect Raspberry Pi version from /proc/cpuinfo.

    Returns:
        int: Pi version (1, 2, 3, 4, or 5), or 4 if unknown/not a Pi.

    Note:
        This function reads /proc/cpuinfo to determine the Pi model.
        Falls back to 4 (conservative speed) if detection fails.
    """
    revision = _get_pi_revision()
    if not revision:
        return 4  # Conservative default

    # Chain of detection strategies
    strategies = [
        _detect_from_new_revision,
        _detect_from_old_revision,
        _detect_from_prefix,
    ]

    for strategy in strategies:
        version = strategy(revision)
        if version is not None:
            return version

    return 4  # Conservative default


def get_spi_speed_for_pi(pi_version: int | None = None, override_hz: int | None = None) -> int:
    """Get appropriate SPI speed for Raspberry Pi version.

    Args:
        pi_version: Pi version (1-5). If None, auto-detects.
        override_hz: Manual speed override in Hz. If provided, uses this instead.

    Returns:
        int: SPI speed in Hz.

    Note:
        Pi 3 can use faster speeds, Pi 4+ needs slower speeds for stability.
        Based on Waveshare wiki recommendations.
    """
    if override_hz is not None:
        return override_hz

    if pi_version is None:
        pi_version = detect_raspberry_pi_version()

    # Use Pi-specific speeds based on Waveshare recommendations
    if pi_version <= 3:
        return SPIConstants.SPI_SPEED_PI3_HZ
    # Pi 4, 5, and unknown versions use conservative speed
    return SPIConstants.SPI_SPEED_PI4_HZ


class GPIOInterface(Protocol):
    """Protocol for GPIO operations."""

    BCM: int
    OUT: int
    IN: int

    def setmode(self, mode: int) -> None:
        """Set the GPIO pin numbering mode.

        Args:
            mode: Pin numbering mode (e.g., BCM).
        """

    def setup(
        self, channel: int | list[int], direction: int, pull_up_down: int = 20, initial: int = -1
    ) -> None:
        """Set up a GPIO pin.

        Args:
            channel: GPIO pin number(s) to configure.
            direction: Pin direction (IN or OUT).
            pull_up_down: Pull resistor configuration (default: 20).
            initial: Initial output value (default: -1).
        """

    def output(self, channel: int | list[int], state: int | bool | list[int] | list[bool]) -> None:
        """Set GPIO pin output value.

        Args:
            channel: GPIO pin number(s) to set.
            state: Output state(s) (0/1, True/False).
        """

    def input(self, channel: int) -> int:
        """Read GPIO pin input value.

        Args:
            channel: GPIO pin number to read.

        Returns:
            int: Pin state (0 or 1).
        """
        ...

    def cleanup(self) -> None:
        """Clean up GPIO resources."""


class SPIDeviceInterface(Protocol):
    """Protocol for SPI device operations."""

    max_speed_hz: int
    mode: int

    def open(self, bus: int, device: int) -> None:
        """Open SPI device.

        Args:
            bus: SPI bus number.
            device: SPI device number.
        """

    def writebytes(self, values: list[int]) -> None:
        """Write bytes to SPI.

        Args:
            values: List of byte values to write.
        """

    def xfer2(
        self, values: list[int], speed_hz: int = 0, delay_usecs: int = 0, bits_per_word: int = 0
    ) -> list[int]:
        """Transfer data to/from SPI.

        Args:
            values: Data to send.
            speed_hz: Transfer speed in Hz (0 = default).
            delay_usecs: Delay between transfers in microseconds.
            bits_per_word: Bits per word (0 = default).

        Returns:
            list[int]: Data received during transfer.
        """
        ...

    def close(self) -> None:
        """Close SPI device."""


class SPIInterface(ABC):
    """Abstract base class for SPI communication.

    Thread Safety:
        SPI interface implementations are NOT thread-safe. The underlying
        hardware (SPI bus and GPIO pins) does not support concurrent access.

        Critical issues with concurrent access:
        - SPI transactions (chip select, data transfer) must be atomic
        - GPIO operations (reset, busy check) can cause race conditions
        - Command/data sequences can be interleaved, corrupting communication

        If you need concurrent access to the display, implement synchronization
        at a higher level (e.g., EPaperDisplay) or use a dedicated thread for
        all SPI operations.
    """

    @abstractmethod
    def init(self) -> None:
        """Initialize SPI interface.

        Sets up GPIO pins, opens SPI device, and performs hardware reset.

        Raises:
            InitializationError: If initialization fails.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close SPI interface and cleanup resources.

        Releases GPIO pins and closes SPI device.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Hardware reset the device.

        Performs a hardware reset by toggling the reset pin.
        """
        pass

    @abstractmethod
    def wait_busy(self, timeout_ms: int = 5000) -> None:
        """Wait for device to be ready.

        Polls the busy pin until device is ready or timeout occurs.

        Args:
            timeout_ms: Maximum wait time in milliseconds.

        Raises:
            IT8951TimeoutError: If timeout occurs.
        """
        pass

    @abstractmethod
    def write_command(self, command: int) -> None:
        """Write a command to the device.

        Args:
            command: Command byte to write.

        Raises:
            CommunicationError: If not initialized.
        """
        pass

    @abstractmethod
    def write_data(self, data: int) -> None:
        """Write data to the device.

        Args:
            data: Data word (16-bit) to write.

        Raises:
            CommunicationError: If not initialized.
        """
        pass

    @abstractmethod
    def write_data_bulk(self, data: list[int]) -> None:
        """Write bulk data to the device.

        Args:
            data: List of data words to write.

        Raises:
            CommunicationError: If not initialized.
        """
        pass

    @abstractmethod
    def read_data(self) -> int:
        """Read data from the device.

        Returns:
            int: Data word (16-bit) read from device.

        Raises:
            CommunicationError: If not initialized.
        """
        pass

    @abstractmethod
    def read_data_bulk(self, length: int) -> list[int]:
        """Read bulk data from the device.

        Args:
            length: Number of data words to read.

        Returns:
            list[int]: List of data words read.

        Raises:
            CommunicationError: If not initialized.
        """
        pass


class RaspberryPiSPI(SPIInterface):
    """SPI interface implementation for Raspberry Pi."""

    def __init__(self, spi_speed_hz: int | None = None) -> None:
        """Initialize Raspberry Pi SPI interface.

        Args:
            spi_speed_hz: Manual SPI speed override in Hz. If None, auto-detects
                         based on Pi version.
        """
        self._gpio: GPIOInterface | None = None
        self._spi: SPIDeviceInterface | None = None
        self._initialized = False
        self._spi_speed_hz = spi_speed_hz

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
            # Auto-detect Pi version and use appropriate speed, or use override
            self._spi.max_speed_hz = get_spi_speed_for_pi(override_hz=self._spi_speed_hz)
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
        time.sleep(TimingConstants.RESET_DURATION_S)
        self._gpio.output(GPIOPin.RESET, 1)
        time.sleep(TimingConstants.RESET_DURATION_S)

    def wait_busy(self, timeout_ms: int = 5000) -> None:
        """Wait for device to be ready."""
        if not self._gpio:
            raise InitializationError("GPIO not initialized")

        start_time = time.time()
        while time.time() - start_time < timeout_ms / 1000:
            if self._gpio.input(GPIOPin.BUSY) == 0:
                return
            time.sleep(TimingConstants.BUSY_POLL_FAST_S)

        raise IT8951TimeoutError(f"Device busy timeout after {timeout_ms}ms")

    def write_command(self, command: int) -> None:
        """Write a command to the device."""
        if not self._spi:
            raise CommunicationError("SPI not initialized")

        self.wait_busy()
        preamble = SPIConstants.PREAMBLE_CMD
        self._spi.writebytes(
            [preamble >> ProtocolConstants.BYTE_SHIFT, preamble & ProtocolConstants.BYTE_MASK]
        )
        self._spi.writebytes(
            [command >> ProtocolConstants.BYTE_SHIFT, command & ProtocolConstants.BYTE_MASK]
        )

    def write_data(self, data: int) -> None:
        """Write data to the device."""
        if not self._spi:
            raise CommunicationError("SPI not initialized")

        self.wait_busy()
        preamble = SPIConstants.PREAMBLE_DATA
        self._spi.writebytes(
            [preamble >> ProtocolConstants.BYTE_SHIFT, preamble & ProtocolConstants.BYTE_MASK]
        )
        self._spi.writebytes(
            [data >> ProtocolConstants.BYTE_SHIFT, data & ProtocolConstants.BYTE_MASK]
        )

    def write_data_bulk(self, data: list[int]) -> None:
        """Write bulk data to the device."""
        if not self._spi:
            raise CommunicationError("SPI not initialized")

        self.wait_busy()
        preamble = SPIConstants.PREAMBLE_DATA
        self._spi.writebytes(
            [preamble >> ProtocolConstants.BYTE_SHIFT, preamble & ProtocolConstants.BYTE_MASK]
        )

        for value in data:
            self._spi.writebytes(
                [value >> ProtocolConstants.BYTE_SHIFT, value & ProtocolConstants.BYTE_MASK]
            )

    def read_data(self) -> int:
        """Read data from the device."""
        if not self._spi:
            raise CommunicationError("SPI not initialized")

        self.wait_busy()
        preamble = SPIConstants.PREAMBLE_READ
        self._spi.writebytes(
            [preamble >> ProtocolConstants.BYTE_SHIFT, preamble & ProtocolConstants.BYTE_MASK]
        )

        dummy = SPIConstants.DUMMY_DATA
        self._spi.writebytes(
            [dummy >> ProtocolConstants.BYTE_SHIFT, dummy & ProtocolConstants.BYTE_MASK]
        )

        result = self._spi.xfer2(SPIConstants.READ_DUMMY_BYTES)
        return (result[0] << ProtocolConstants.BYTE_SHIFT) | result[1]

    def read_data_bulk(self, length: int) -> list[int]:
        """Read bulk data from the device."""
        if not self._spi:
            raise CommunicationError("SPI not initialized")

        self.wait_busy()
        preamble = SPIConstants.PREAMBLE_READ
        self._spi.writebytes(
            [preamble >> ProtocolConstants.BYTE_SHIFT, preamble & ProtocolConstants.BYTE_MASK]
        )

        dummy = SPIConstants.DUMMY_DATA
        self._spi.writebytes(
            [dummy >> ProtocolConstants.BYTE_SHIFT, dummy & ProtocolConstants.BYTE_MASK]
        )

        data: list[int] = []
        for _ in range(length):
            result = self._spi.xfer2(SPIConstants.READ_DUMMY_BYTES)
            data.append((result[0] << ProtocolConstants.BYTE_SHIFT) | result[1])

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
        time.sleep(TimingConstants.RESET_DURATION_S)

    def wait_busy(self, timeout_ms: int = 5000) -> None:
        """Simulate waiting for device ready."""
        # Mock implementation ignores timeout_ms parameter
        _ = timeout_ms  # Unused in mock
        if self._busy:
            time.sleep(0.01)
            self._busy = False

    def write_command(self, command: int) -> None:
        """Simulate writing a command."""
        if not self._initialized:
            raise CommunicationError("Mock SPI not initialized")

        self.wait_busy()
        self._last_command = command
        self._busy = True

    def write_data(self, data: int) -> None:
        """Simulate writing data."""
        if not self._initialized:
            raise CommunicationError("Mock SPI not initialized")

        self.wait_busy()
        self._data_buffer.append(data)

    def write_data_bulk(self, data: list[int]) -> None:
        """Simulate writing bulk data."""
        if not self._initialized:
            raise CommunicationError("Mock SPI not initialized")

        self.wait_busy()
        self._data_buffer.extend(data)

    def read_data(self) -> int:
        """Simulate reading data."""
        if not self._initialized:
            raise CommunicationError("Mock SPI not initialized")

        self.wait_busy()
        if self._read_data:
            return self._read_data.pop(0)
        return SPIConstants.MOCK_DEFAULT_VALUE

    def read_data_bulk(self, length: int) -> list[int]:
        """Simulate reading bulk data."""
        if not self._initialized:
            raise CommunicationError("Mock SPI not initialized")

        self.wait_busy()
        data: list[int] = []
        for _ in range(length):
            if self._read_data:
                data.append(self._read_data.pop(0))
            else:
                data.append(SPIConstants.MOCK_DEFAULT_VALUE)
        return data

    def set_read_data(self, data: list[int]) -> None:
        """Set data to be returned by read operations (for testing).

        Args:
            data: List of data words to queue for reading.
        """
        self._read_data.extend(data)

    def get_last_command(self) -> int | None:
        """Get the last command written (for testing).

        Returns:
            int | None: Last command byte written, or None if no commands.
        """
        return self._last_command

    def get_data_buffer(self) -> list[int]:
        """Get the data buffer (for testing).

        Returns:
            list[int]: Copy of all data written to the device.
        """
        return self._data_buffer.copy()


def create_spi_interface(spi_speed_hz: int | None = None) -> SPIInterface:
    """Create appropriate SPI interface based on platform.

    Automatically selects the correct SPI implementation:
    - RaspberryPiSPI for ARM Linux systems (Raspberry Pi)
    - MockSPI for all other platforms (development/testing)

    Args:
        spi_speed_hz: Manual SPI speed override in Hz. Only used for RaspberryPiSPI.
                     If None, auto-detects based on Pi version.

    Returns:
        SPIInterface: Appropriate SPI interface instance.

    Examples:
        >>> # Auto-detect Pi version and use appropriate speed
        >>> spi = create_spi_interface()
        >>> spi.init()
        >>> # Use spi for communication
        >>> spi.close()

        >>> # Manual speed override
        >>> spi = create_spi_interface(spi_speed_hz=10000000)  # 10MHz
        >>> spi.init()
    """
    if sys.platform == "linux":
        import platform

        machine = platform.machine().lower()
        # Check for ARM architecture (not sensitive - just CPU detection)
        # CodeQL: This is not sensitive information, just platform detection
        if "arm" in machine or "aarch" in machine:  # nosec
            return RaspberryPiSPI(spi_speed_hz=spi_speed_hz)
    return MockSPI()
