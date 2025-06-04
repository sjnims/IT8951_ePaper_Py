"""Tests for SPI interface module."""

import sys
import time

import pytest
from pytest_mock import MockerFixture

from IT8951_ePaper_Py.constants import GPIOPin, SPIConstants
from IT8951_ePaper_Py.exceptions import CommunicationError, InitializationError, IT8951TimeoutError
from IT8951_ePaper_Py.spi_interface import (
    MockSPI,
    RaspberryPiSPI,
    create_spi_interface,
    detect_raspberry_pi_version,
    get_spi_speed_for_pi,
)


class TestMockSPI:
    """Test MockSPI implementation."""

    def test_init(self) -> None:
        """Test MockSPI initialization."""
        spi = MockSPI()
        assert not spi._initialized  # type: ignore[reportPrivateUsage]

        spi.init()
        assert spi._initialized  # type: ignore[reportPrivateUsage]

        spi.init()
        assert spi._initialized  # type: ignore[reportPrivateUsage]

    def test_close(self) -> None:
        """Test MockSPI close."""
        spi = MockSPI()
        spi.init()
        spi.write_command(0x1234)
        spi.write_data(0x5678)

        spi.close()
        assert not spi._initialized  # type: ignore[reportPrivateUsage]
        assert spi.get_last_command() is None
        assert len(spi.get_data_buffer()) == 0

    @pytest.mark.slow
    def test_reset(self) -> None:
        """Test hardware reset simulation."""
        spi = MockSPI()
        spi.init()
        spi._busy = True  # type: ignore[reportPrivateUsage]

        start = time.time()
        spi.reset()
        elapsed = time.time() - start

        assert not spi._busy  # type: ignore[reportPrivateUsage]
        assert elapsed >= 0.1

    def test_wait_busy(self) -> None:
        """Test wait busy simulation."""
        spi = MockSPI()
        spi.init()
        spi._busy = True  # type: ignore[reportPrivateUsage]

        spi.wait_busy()
        assert not spi._busy  # type: ignore[reportPrivateUsage]

    def test_write_command(self) -> None:
        """Test command writing."""
        spi = MockSPI()

        with pytest.raises(CommunicationError):
            spi.write_command(0x1234)

        spi.init()
        spi.write_command(0x1234)
        assert spi.get_last_command() == 0x1234

    def test_write_data(self) -> None:
        """Test data writing."""
        spi = MockSPI()
        spi.init()

        spi.write_data(0x1234)
        spi.write_data(0x5678)

        buffer = spi.get_data_buffer()
        assert buffer == [0x1234, 0x5678]

    def test_write_data_bulk(self) -> None:
        """Test bulk data writing."""
        spi = MockSPI()
        spi.init()

        data = [0x1111, 0x2222, 0x3333]
        spi.write_data_bulk(data)

        buffer = spi.get_data_buffer()
        assert buffer == data

    def test_read_data(self) -> None:
        """Test data reading."""
        spi = MockSPI()
        spi.init()

        assert spi.read_data() == 0xFFFF

        spi.set_read_data([0x1234, 0x5678])
        assert spi.read_data() == 0x1234
        assert spi.read_data() == 0x5678
        assert spi.read_data() == 0xFFFF

    def test_read_data_bulk(self) -> None:
        """Test bulk data reading."""
        spi = MockSPI()
        spi.init()

        spi.set_read_data([0x1111, 0x2222, 0x3333])
        data = spi.read_data_bulk(5)

        assert data == [0x1111, 0x2222, 0x3333, 0xFFFF, 0xFFFF]

    def test_write_data_without_init(self) -> None:
        """Test write_data fails without initialization."""
        spi = MockSPI()
        with pytest.raises(CommunicationError):
            spi.write_data(0x1234)

    def test_write_data_bulk_without_init(self) -> None:
        """Test write_data_bulk fails without initialization."""
        spi = MockSPI()
        with pytest.raises(CommunicationError):
            spi.write_data_bulk([0x1234])

    def test_read_data_without_init(self) -> None:
        """Test read_data fails without initialization."""
        spi = MockSPI()
        with pytest.raises(CommunicationError):
            spi.read_data()

    def test_read_data_bulk_without_init(self) -> None:
        """Test read_data_bulk fails without initialization."""
        spi = MockSPI()
        with pytest.raises(CommunicationError):
            spi.read_data_bulk(5)


class TestRaspberryPiSPI:
    """Test RaspberryPiSPI implementation."""

    @pytest.mark.skipif(
        sys.platform != "linux" or "arm" not in sys.platform,
        reason="Requires Raspberry Pi hardware",
    )
    def test_init_on_pi(self) -> None:
        """Test initialization on actual Raspberry Pi."""
        spi = RaspberryPiSPI()
        spi.init()
        assert spi._initialized  # type: ignore[reportPrivateUsage]
        spi.close()

    def test_init_without_hardware(self, mocker: MockerFixture) -> None:
        """Test initialization fails gracefully without hardware."""
        mocker.patch("builtins.__import__", side_effect=ImportError("No module"))

        spi = RaspberryPiSPI()
        with pytest.raises(InitializationError) as exc_info:
            spi.init()

        assert "Failed to import required modules" in str(exc_info.value)

    def test_operations_without_init(self) -> None:
        """Test operations fail without initialization."""
        spi = RaspberryPiSPI()

        with pytest.raises(InitializationError):
            spi.reset()

        with pytest.raises(InitializationError):
            spi.wait_busy()

        with pytest.raises(CommunicationError):
            spi.write_command(0x1234)

    def test_mock_gpio_operations(self, mocker: MockerFixture) -> None:
        """Test GPIO operations with mocked hardware."""
        mock_gpio = mocker.MagicMock()
        mock_gpio.BCM = 11
        mock_gpio.OUT = 0
        mock_gpio.IN = 1

        mock_spidev_class = mocker.MagicMock()
        mock_spi_instance = mocker.MagicMock()
        mock_spidev_class.SpiDev.return_value = mock_spi_instance

        mocker.patch.dict(
            "sys.modules",
            {
                "RPi": mocker.MagicMock(GPIO=mock_gpio),
                "RPi.GPIO": mock_gpio,
                "spidev": mock_spidev_class,
            },
        )

        spi = RaspberryPiSPI()
        spi.init()

        mock_gpio.setmode.assert_called_once()
        mock_gpio.setup.assert_any_call(GPIOPin.RESET, mock_gpio.OUT)
        mock_gpio.setup.assert_any_call(GPIOPin.BUSY, mock_gpio.IN)

        spi.close()
        mock_gpio.cleanup.assert_called_once()

    def test_init_already_initialized(self, mocker: MockerFixture) -> None:
        """Test init when already initialized."""
        mock_gpio = mocker.MagicMock()
        mock_gpio.BCM = 11
        mock_gpio.OUT = 0
        mock_gpio.IN = 1

        mock_spidev_class = mocker.MagicMock()
        mock_spi_instance = mocker.MagicMock()
        mock_spidev_class.SpiDev.return_value = mock_spi_instance

        mocker.patch.dict(
            "sys.modules",
            {
                "RPi": mocker.MagicMock(GPIO=mock_gpio),
                "RPi.GPIO": mock_gpio,
                "spidev": mock_spidev_class,
            },
        )

        spi = RaspberryPiSPI()
        spi.init()

        # Clear the call counts
        mock_gpio.setmode.reset_mock()

        # Init again - should return early
        spi.init()

        # Should not call setmode again
        mock_gpio.setmode.assert_not_called()

        spi.close()

    def test_init_general_exception(self, mocker: MockerFixture) -> None:
        """Test init with general exception."""
        mock_gpio = mocker.MagicMock()
        mock_gpio.BCM = 11
        mock_gpio.OUT = 0
        mock_gpio.IN = 1
        mock_gpio.setmode.side_effect = Exception("Hardware error")

        mocker.patch.dict(
            "sys.modules",
            {
                "RPi": mocker.MagicMock(GPIO=mock_gpio),
                "RPi.GPIO": mock_gpio,
                "spidev": mocker.MagicMock(),
            },
        )

        spi = RaspberryPiSPI()
        with pytest.raises(InitializationError) as exc_info:
            spi.init()

        assert "Failed to initialize SPI" in str(exc_info.value)
        assert "Hardware error" in str(exc_info.value)

    @pytest.mark.slow
    def test_reset_with_hardware(self, mocker: MockerFixture) -> None:
        """Test hardware reset with mocked GPIO."""
        mock_gpio = mocker.MagicMock()
        mock_gpio.BCM = 11
        mock_gpio.OUT = 0
        mock_gpio.IN = 1

        mock_spidev_class = mocker.MagicMock()
        mock_spi_instance = mocker.MagicMock()
        mock_spidev_class.SpiDev.return_value = mock_spi_instance

        mocker.patch.dict(
            "sys.modules",
            {
                "RPi": mocker.MagicMock(GPIO=mock_gpio),
                "RPi.GPIO": mock_gpio,
                "spidev": mock_spidev_class,
            },
        )

        spi = RaspberryPiSPI()
        spi.init()

        # Clear previous calls from init
        mock_gpio.output.reset_mock()

        # Test reset
        start = time.time()
        spi.reset()
        elapsed = time.time() - start

        # Should set RESET low, wait, then high
        assert mock_gpio.output.call_count == 2
        mock_gpio.output.assert_any_call(GPIOPin.RESET, 0)
        mock_gpio.output.assert_any_call(GPIOPin.RESET, 1)
        assert elapsed >= 0.2  # Two 0.1s sleeps

        spi.close()

    def test_wait_busy_timeout(self, mocker: MockerFixture) -> None:
        """Test wait_busy timeout scenario."""
        mock_gpio = mocker.MagicMock()
        mock_gpio.BCM = 11
        mock_gpio.OUT = 0
        mock_gpio.IN = 1
        mock_gpio.input.return_value = 1  # Always busy

        mock_spidev_class = mocker.MagicMock()
        mock_spi_instance = mocker.MagicMock()
        mock_spidev_class.SpiDev.return_value = mock_spi_instance

        mocker.patch.dict(
            "sys.modules",
            {
                "RPi": mocker.MagicMock(GPIO=mock_gpio),
                "RPi.GPIO": mock_gpio,
                "spidev": mock_spidev_class,
            },
        )

        spi = RaspberryPiSPI()
        spi.init()

        with pytest.raises(IT8951TimeoutError) as exc_info:
            spi.wait_busy(timeout_ms=100)

        assert "Device busy timeout after 100ms" in str(exc_info.value)
        spi.close()

    def test_wait_busy_success(self, mocker: MockerFixture) -> None:
        """Test successful wait_busy."""
        mock_gpio = mocker.MagicMock()
        mock_gpio.BCM = 11
        mock_gpio.OUT = 0
        mock_gpio.IN = 1
        mock_gpio.input.side_effect = [1, 1, 0]  # Busy twice, then ready

        mock_spidev_class = mocker.MagicMock()
        mock_spi_instance = mocker.MagicMock()
        mock_spidev_class.SpiDev.return_value = mock_spi_instance

        mocker.patch.dict(
            "sys.modules",
            {
                "RPi": mocker.MagicMock(GPIO=mock_gpio),
                "RPi.GPIO": mock_gpio,
                "spidev": mock_spidev_class,
            },
        )

        spi = RaspberryPiSPI()
        spi.init()

        spi.wait_busy()
        assert mock_gpio.input.call_count == 3

        spi.close()

    def test_write_command_with_hardware(self, mocker: MockerFixture) -> None:
        """Test write_command with mocked hardware."""
        mock_gpio = mocker.MagicMock()
        mock_gpio.BCM = 11
        mock_gpio.OUT = 0
        mock_gpio.IN = 1
        mock_gpio.input.return_value = 0  # Not busy

        mock_spidev_class = mocker.MagicMock()
        mock_spi_instance = mocker.MagicMock()
        mock_spidev_class.SpiDev.return_value = mock_spi_instance

        mocker.patch.dict(
            "sys.modules",
            {
                "RPi": mocker.MagicMock(GPIO=mock_gpio),
                "RPi.GPIO": mock_gpio,
                "spidev": mock_spidev_class,
            },
        )

        spi = RaspberryPiSPI()
        spi.init()

        spi.write_command(0x1234)

        # Should write preamble and command
        assert mock_spi_instance.writebytes.call_count == 2
        # Preamble
        mock_spi_instance.writebytes.assert_any_call([0x60, 0x00])
        # Command
        mock_spi_instance.writebytes.assert_any_call([0x12, 0x34])

        spi.close()

    def test_write_data_with_hardware(self, mocker: MockerFixture) -> None:
        """Test write_data with mocked hardware."""
        mock_gpio = mocker.MagicMock()
        mock_gpio.BCM = 11
        mock_gpio.OUT = 0
        mock_gpio.IN = 1
        mock_gpio.input.return_value = 0  # Not busy

        mock_spidev_class = mocker.MagicMock()
        mock_spi_instance = mocker.MagicMock()
        mock_spidev_class.SpiDev.return_value = mock_spi_instance

        mocker.patch.dict(
            "sys.modules",
            {
                "RPi": mocker.MagicMock(GPIO=mock_gpio),
                "RPi.GPIO": mock_gpio,
                "spidev": mock_spidev_class,
            },
        )

        spi = RaspberryPiSPI()
        spi.init()

        spi.write_data(0x5678)

        # Should write preamble and data
        assert mock_spi_instance.writebytes.call_count == 2
        # Preamble
        mock_spi_instance.writebytes.assert_any_call([0x00, 0x00])
        # Data
        mock_spi_instance.writebytes.assert_any_call([0x56, 0x78])

        spi.close()

    def test_write_data_bulk_with_hardware(self, mocker: MockerFixture) -> None:
        """Test write_data_bulk with mocked hardware."""
        mock_gpio = mocker.MagicMock()
        mock_gpio.BCM = 11
        mock_gpio.OUT = 0
        mock_gpio.IN = 1
        mock_gpio.input.return_value = 0  # Not busy

        mock_spidev_class = mocker.MagicMock()
        mock_spi_instance = mocker.MagicMock()
        mock_spidev_class.SpiDev.return_value = mock_spi_instance

        mocker.patch.dict(
            "sys.modules",
            {
                "RPi": mocker.MagicMock(GPIO=mock_gpio),
                "RPi.GPIO": mock_gpio,
                "spidev": mock_spidev_class,
            },
        )

        spi = RaspberryPiSPI()
        spi.init()

        data = [0x1111, 0x2222, 0x3333]
        spi.write_data_bulk(data)

        # Should write preamble + 3 data values = 4 calls
        assert mock_spi_instance.writebytes.call_count == 4
        # Preamble
        mock_spi_instance.writebytes.assert_any_call([0x00, 0x00])
        # Data values
        mock_spi_instance.writebytes.assert_any_call([0x11, 0x11])
        mock_spi_instance.writebytes.assert_any_call([0x22, 0x22])
        mock_spi_instance.writebytes.assert_any_call([0x33, 0x33])

        spi.close()

    def test_read_data_with_hardware(self, mocker: MockerFixture) -> None:
        """Test read_data with mocked hardware."""
        mock_gpio = mocker.MagicMock()
        mock_gpio.BCM = 11
        mock_gpio.OUT = 0
        mock_gpio.IN = 1
        mock_gpio.input.return_value = 0  # Not busy

        mock_spidev_class = mocker.MagicMock()
        mock_spi_instance = mocker.MagicMock()
        mock_spi_instance.xfer2.return_value = [0xAB, 0xCD]
        mock_spidev_class.SpiDev.return_value = mock_spi_instance

        mocker.patch.dict(
            "sys.modules",
            {
                "RPi": mocker.MagicMock(GPIO=mock_gpio),
                "RPi.GPIO": mock_gpio,
                "spidev": mock_spidev_class,
            },
        )

        spi = RaspberryPiSPI()
        spi.init()

        result = spi.read_data()

        # Should write preamble and dummy, then read
        assert mock_spi_instance.writebytes.call_count == 2
        # Read preamble
        mock_spi_instance.writebytes.assert_any_call([0x10, 0x00])
        # Dummy data
        mock_spi_instance.writebytes.assert_any_call([0x00, 0x00])

        # Should transfer to read result
        mock_spi_instance.xfer2.assert_called_once_with([0x00, 0x00])
        assert result == 0xABCD

        spi.close()

    def test_read_data_bulk_with_hardware(self, mocker: MockerFixture) -> None:
        """Test read_data_bulk with mocked hardware."""
        mock_gpio = mocker.MagicMock()
        mock_gpio.BCM = 11
        mock_gpio.OUT = 0
        mock_gpio.IN = 1
        mock_gpio.input.return_value = 0  # Not busy

        mock_spidev_class = mocker.MagicMock()
        mock_spi_instance = mocker.MagicMock()
        mock_spi_instance.xfer2.side_effect = [
            [0x11, 0x11],
            [0x22, 0x22],
            [0x33, 0x33],
        ]
        mock_spidev_class.SpiDev.return_value = mock_spi_instance

        mocker.patch.dict(
            "sys.modules",
            {
                "RPi": mocker.MagicMock(GPIO=mock_gpio),
                "RPi.GPIO": mock_gpio,
                "spidev": mock_spidev_class,
            },
        )

        spi = RaspberryPiSPI()
        spi.init()

        result = spi.read_data_bulk(3)

        # Should write preamble and dummy
        assert mock_spi_instance.writebytes.call_count == 2
        # Read preamble
        mock_spi_instance.writebytes.assert_any_call([0x10, 0x00])
        # Dummy data
        mock_spi_instance.writebytes.assert_any_call([0x00, 0x00])

        # Should transfer 3 times
        assert mock_spi_instance.xfer2.call_count == 3
        assert result == [0x1111, 0x2222, 0x3333]

        spi.close()

    def test_write_data_without_init(self) -> None:
        """Test write_data fails without initialization."""
        spi = RaspberryPiSPI()
        with pytest.raises(CommunicationError):
            spi.write_data(0x1234)

    def test_write_data_bulk_without_init(self) -> None:
        """Test write_data_bulk fails without initialization."""
        spi = RaspberryPiSPI()
        with pytest.raises(CommunicationError):
            spi.write_data_bulk([0x1234])

    def test_read_data_without_init(self) -> None:
        """Test read_data fails without initialization."""
        spi = RaspberryPiSPI()
        with pytest.raises(CommunicationError):
            spi.read_data()

    def test_read_data_bulk_without_init(self) -> None:
        """Test read_data_bulk fails without initialization."""
        spi = RaspberryPiSPI()
        with pytest.raises(CommunicationError):
            spi.read_data_bulk(5)

    def test_close_partial_init(self, mocker: MockerFixture) -> None:
        """Test close when only partially initialized."""
        mock_gpio = mocker.MagicMock()
        mock_gpio.BCM = 11
        mock_gpio.OUT = 0
        mock_gpio.IN = 1

        mocker.patch.dict(
            "sys.modules",
            {
                "RPi": mocker.MagicMock(GPIO=mock_gpio),
                "RPi.GPIO": mock_gpio,
                "spidev": mocker.MagicMock(),
            },
        )

        spi = RaspberryPiSPI()
        spi._gpio = mock_gpio  # type: ignore[reportPrivateUsage]
        spi._spi = None  # type: ignore[reportPrivateUsage]

        spi.close()

        mock_gpio.cleanup.assert_called_once()
        assert spi._gpio is None  # type: ignore[reportPrivateUsage]


class TestCreateSPIInterface:
    """Test SPI interface factory function."""

    def test_create_mock_on_non_linux(self, mocker: MockerFixture) -> None:
        """Test MockSPI is created on non-Linux platforms."""
        mocker.patch("sys.platform", "darwin")
        spi = create_spi_interface()
        assert isinstance(spi, MockSPI)

    def test_create_mock_on_non_arm_linux(self, mocker: MockerFixture) -> None:
        """Test MockSPI is created on non-ARM Linux."""
        mocker.patch("sys.platform", "linux")
        mocker.patch("platform.machine", return_value="x86_64")
        spi = create_spi_interface()
        assert isinstance(spi, MockSPI)

    @pytest.mark.skipif(
        sys.platform != "linux" or "arm" not in sys.platform,
        reason="Requires ARM Linux",
    )
    def test_create_raspberry_pi_on_arm_linux(self) -> None:
        """Test RaspberryPiSPI is created on ARM Linux."""
        spi = create_spi_interface()
        assert isinstance(spi, RaspberryPiSPI)

    def test_create_raspberry_pi_on_arm_linux_mocked(self, mocker: MockerFixture) -> None:
        """Test RaspberryPiSPI is created on ARM Linux using mocked platform."""
        mocker.patch("sys.platform", "linux")
        mocker.patch("platform.machine", return_value="armv7l")
        spi = create_spi_interface()
        assert isinstance(spi, RaspberryPiSPI)

    def test_create_raspberry_pi_on_aarch64_linux_mocked(self, mocker: MockerFixture) -> None:
        """Test RaspberryPiSPI is created on aarch64 Linux using mocked platform."""
        mocker.patch("sys.platform", "linux")
        mocker.patch("platform.machine", return_value="aarch64")
        spi = create_spi_interface()
        assert isinstance(spi, RaspberryPiSPI)

    def test_create_with_speed_override(self, mocker: MockerFixture) -> None:
        """Test creating interface with manual speed override."""
        mocker.patch("sys.platform", "linux")
        mocker.patch("platform.machine", return_value="armv7l")
        spi = create_spi_interface(spi_speed_hz=10000000)
        assert isinstance(spi, RaspberryPiSPI)


class TestPiDetection:
    """Test Raspberry Pi version detection and speed selection."""

    def test_detect_pi_3(self, mocker: MockerFixture) -> None:
        """Test detecting Raspberry Pi 3."""
        cpuinfo = """processor       : 0
model name      : ARMv7 Processor rev 4 (v7l)
BogoMIPS        : 76.80
Features        : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm crc32
CPU implementer : 0x41
CPU architecture: 7
CPU variant     : 0x0
CPU part        : 0xd08
CPU revision    : 3

Hardware        : BCM2835
Revision        : a32082
Serial          : 00000000abcdef12
Model           : Raspberry Pi 3 Model B Rev 1.2
"""
        mock_open = mocker.mock_open(read_data=cpuinfo)
        mocker.patch("builtins.open", mock_open)

        version = detect_raspberry_pi_version()
        assert version == 3

    def test_detect_pi_4(self, mocker: MockerFixture) -> None:
        """Test detecting Raspberry Pi 4."""
        cpuinfo = """processor       : 0
model name      : ARMv7 Processor rev 3 (v7l)
BogoMIPS        : 108.00
Features        : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm crc32
CPU implementer : 0x41
CPU architecture: 7
CPU variant     : 0x0
CPU part        : 0xd08
CPU revision    : 3

Hardware        : BCM2711
Revision        : c03112
Serial          : 100000001234abcd
Model           : Raspberry Pi 4 Model B Rev 1.2
"""
        mock_open = mocker.mock_open(read_data=cpuinfo)
        mocker.patch("builtins.open", mock_open)

        version = detect_raspberry_pi_version()
        assert version == 4

    def test_detect_pi_5(self, mocker: MockerFixture) -> None:
        """Test detecting Raspberry Pi 5."""
        cpuinfo = """processor       : 0
BogoMIPS        : 108.00
Features        : fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid asimdrdm lrcpc dcpop asimddp
CPU implementer : 0x41
CPU architecture: 8
CPU variant     : 0x4
CPU part        : 0xd0b
CPU revision    : 1

Hardware        : BCM2712
Revision        : c04170
Serial          : 100000001234abcd
Model           : Raspberry Pi 5 Model B Rev 1.0
"""
        mock_open = mocker.mock_open(read_data=cpuinfo)
        mocker.patch("builtins.open", mock_open)

        version = detect_raspberry_pi_version()
        assert version == 5

    def test_detect_unknown_pi(self, mocker: MockerFixture) -> None:
        """Test detecting unknown Pi returns 4 (conservative)."""
        cpuinfo = """processor       : 0
model name      : Unknown Processor
Revision        : unknown123
"""
        mock_open = mocker.mock_open(read_data=cpuinfo)
        mocker.patch("builtins.open", mock_open)

        version = detect_raspberry_pi_version()
        assert version == 4  # Conservative default

    def test_detect_no_revision(self, mocker: MockerFixture) -> None:
        """Test handling missing revision info."""
        cpuinfo = """processor       : 0
model name      : ARMv7 Processor
"""
        mock_open = mocker.mock_open(read_data=cpuinfo)
        mocker.patch("builtins.open", mock_open)

        version = detect_raspberry_pi_version()
        assert version == 4  # Conservative default

    def test_detect_short_revision_string(self, mocker: MockerFixture) -> None:
        """Test handling short revision strings (less than 6 chars) to cover line 64."""
        cpuinfo = """processor       : 0
model name      : ARMv7 Processor
Revision        : a32
"""
        mock_open = mocker.mock_open(read_data=cpuinfo)
        mocker.patch("builtins.open", mock_open)

        version = detect_raspberry_pi_version()
        assert version == 4  # Should fall back to conservative default

    def test_detect_file_error(self, mocker: MockerFixture) -> None:
        """Test handling file read error."""
        mocker.patch("builtins.open", side_effect=OSError("File not found"))

        version = detect_raspberry_pi_version()
        assert version == 4  # Conservative default

    def test_get_spi_speed_pi3(self) -> None:
        """Test getting SPI speed for Pi 3."""
        speed = get_spi_speed_for_pi(pi_version=3)
        assert speed == SPIConstants.SPI_SPEED_PI3_HZ

    def test_get_spi_speed_pi4(self) -> None:
        """Test getting SPI speed for Pi 4."""
        speed = get_spi_speed_for_pi(pi_version=4)
        assert speed == SPIConstants.SPI_SPEED_PI4_HZ

    def test_get_spi_speed_pi5(self) -> None:
        """Test getting SPI speed for Pi 5."""
        speed = get_spi_speed_for_pi(pi_version=5)
        assert speed == SPIConstants.SPI_SPEED_PI4_HZ  # Uses conservative speed

    def test_get_spi_speed_override(self) -> None:
        """Test SPI speed override."""
        speed = get_spi_speed_for_pi(pi_version=3, override_hz=10000000)
        assert speed == 10000000

    def test_get_spi_speed_auto_detect(self, mocker: MockerFixture) -> None:
        """Test SPI speed with auto-detection."""
        mocker.patch("IT8951_ePaper_Py.spi_interface.detect_raspberry_pi_version", return_value=3)

        speed = get_spi_speed_for_pi()
        assert speed == SPIConstants.SPI_SPEED_PI3_HZ


class TestRaspberryPiSPIWithSpeed:
    """Test RaspberryPiSPI with speed configuration."""

    def test_init_with_auto_speed(self, mocker: MockerFixture) -> None:
        """Test RaspberryPiSPI initialization with auto-detected speed."""
        mock_gpio = mocker.MagicMock()
        mock_gpio.BCM = 11
        mock_gpio.OUT = 0
        mock_gpio.IN = 1
        mock_gpio.input.return_value = 0  # Not busy

        mock_spidev_class = mocker.MagicMock()
        mock_spi_instance = mocker.MagicMock()
        mock_spidev_class.SpiDev.return_value = mock_spi_instance

        mocker.patch.dict(
            "sys.modules",
            {
                "RPi": mocker.MagicMock(GPIO=mock_gpio),
                "RPi.GPIO": mock_gpio,
                "spidev": mock_spidev_class,
            },
        )

        # Mock Pi version detection to return Pi 3
        mocker.patch("IT8951_ePaper_Py.spi_interface.detect_raspberry_pi_version", return_value=3)

        spi = RaspberryPiSPI()
        spi.init()

        # Should use Pi 3 speed
        assert mock_spi_instance.max_speed_hz == SPIConstants.SPI_SPEED_PI3_HZ

        spi.close()

    def test_init_with_manual_speed(self, mocker: MockerFixture) -> None:
        """Test RaspberryPiSPI initialization with manual speed override."""
        mock_gpio = mocker.MagicMock()
        mock_gpio.BCM = 11
        mock_gpio.OUT = 0
        mock_gpio.IN = 1
        mock_gpio.input.return_value = 0  # Not busy

        mock_spidev_class = mocker.MagicMock()
        mock_spi_instance = mocker.MagicMock()
        mock_spidev_class.SpiDev.return_value = mock_spi_instance

        mocker.patch.dict(
            "sys.modules",
            {
                "RPi": mocker.MagicMock(GPIO=mock_gpio),
                "RPi.GPIO": mock_gpio,
                "spidev": mock_spidev_class,
            },
        )

        spi = RaspberryPiSPI(spi_speed_hz=10000000)
        spi.init()

        # Should use manual override speed
        assert mock_spi_instance.max_speed_hz == 10000000

        spi.close()
