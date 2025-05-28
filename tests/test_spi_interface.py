"""Tests for SPI interface module."""

import sys
import time

import pytest
from pytest_mock import MockerFixture

from IT8951_ePaper_Py.constants import GPIOPin
from IT8951_ePaper_Py.exceptions import InitializationError
from IT8951_ePaper_Py.spi_interface import MockSPI, RaspberryPiSPI, create_spi_interface


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

        with pytest.raises(InitializationError):
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

        with pytest.raises(InitializationError):
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
