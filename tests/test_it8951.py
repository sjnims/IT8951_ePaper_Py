"""Tests for IT8951 core driver."""

import pytest

from IT8951_ePaper_Py.constants import (
    DisplayMode,
    MemoryConstants,
    PixelFormat,
    SystemCommand,
)
from IT8951_ePaper_Py.exceptions import (
    InitializationError,
    InvalidParameterError,
)
from IT8951_ePaper_Py.it8951 import IT8951
from IT8951_ePaper_Py.models import (
    DeviceInfo,
    DisplayArea,
    LoadImageInfo,
)
from IT8951_ePaper_Py.spi_interface import MockSPI


class TestIT8951:
    """Test IT8951 driver."""

    @pytest.fixture
    def mock_spi(self) -> MockSPI:
        """Create mock SPI interface."""
        return MockSPI()

    @pytest.fixture
    def driver(self, mock_spi: MockSPI) -> IT8951:
        """Create IT8951 driver with mock SPI."""
        return IT8951(mock_spi)

    def test_init(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test driver initialization."""
        mock_spi.set_read_data(
            [
                1024,  # panel_width
                768,  # panel_height
                0x36E0,  # memory_addr_l
                0x0012,  # memory_addr_h
                49,
                46,
                48,
                0,
                0,
                0,
                0,
                0,  # fw_version "1.0"
                50,
                46,
                48,
                0,
                0,
                0,
                0,
                0,  # lut_version "2.0"
            ]
        )
        mock_spi.set_read_data([0x0000])  # REG_0204 read

        info = driver.init()

        assert info.panel_width == 1024
        assert info.panel_height == 768
        assert info.memory_address == 0x001236E0
        assert info.fw_version == "1.0"
        assert info.lut_version == "2.0"

        assert mock_spi.get_last_command() == SystemCommand.REG_WR

        info2 = driver.init()
        assert info2 == info

    def test_init_failure(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test initialization failure handling."""
        mock_spi.init = lambda: (_ for _ in ()).throw(Exception("SPI failed"))

        with pytest.raises(InitializationError) as exc_info:
            driver.init()

        assert "Failed to initialize IT8951" in str(exc_info.value)

    def test_close(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test driver close."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()
        driver.close()

        assert not driver._initialized  # type: ignore[reportPrivateUsage]
        assert driver._device_info is None  # type: ignore[reportPrivateUsage]

    def test_operations_without_init(self, driver: IT8951) -> None:
        """Test operations fail without initialization."""
        with pytest.raises(InitializationError):
            driver.standby()

        with pytest.raises(InitializationError):
            driver.sleep()

        with pytest.raises(InitializationError):
            driver.get_vcom()

    def test_standby(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test standby mode."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()
        driver.standby()

        assert mock_spi.get_last_command() == SystemCommand.STANDBY

    def test_sleep(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test sleep mode."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()
        driver.sleep()

        assert mock_spi.get_last_command() == SystemCommand.SLEEP

    def test_vcom_operations(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test VCOM voltage operations."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()

        mock_spi.set_read_data([2500])
        voltage = driver.get_vcom()
        assert voltage == -2.5

        driver.set_vcom(-3.0)
        buffer = mock_spi.get_data_buffer()
        assert 3000 in buffer

        with pytest.raises(InvalidParameterError):
            driver.set_vcom(-6.0)

    def test_load_image(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test image loading operations."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()

        info = LoadImageInfo(
            source_buffer=b"\x00\x01\x02\x03",
            target_memory_addr=MemoryConstants.IMAGE_BUFFER_ADDR,
            pixel_format=PixelFormat.BPP_8,
        )

        driver.load_image_start(info)
        driver.load_image_write(info.source_buffer)
        driver.load_image_end()

        assert mock_spi.get_last_command() == SystemCommand.LD_IMG_END

    def test_display_area(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test display area operation."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()

        area = DisplayArea(
            x=0,
            y=0,
            width=800,
            height=600,
            mode=DisplayMode.GC16,
        )

        mock_spi.set_read_data([0])
        driver.display_area(area, wait=True)

        assert mock_spi.get_last_command() == SystemCommand.REG_RD
        buffer = mock_spi.get_data_buffer()
        assert 800 in buffer
        assert 600 in buffer

    def test_display_area_validation(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test display area validation."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()

        area = DisplayArea(
            x=800,
            y=0,
            width=800,
            height=600,
        )

        with pytest.raises(InvalidParameterError) as exc_info:
            driver.display_area(area)

        assert "exceeds panel width" in str(exc_info.value)

    def test_device_info_property(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test device info property."""
        with pytest.raises(InitializationError):
            _ = driver.device_info

        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()

        info = driver.device_info
        assert isinstance(info, DeviceInfo)
        assert info.panel_width == 1024
