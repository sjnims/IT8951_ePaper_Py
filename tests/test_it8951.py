"""Tests for IT8951 core driver."""

import pytest

from IT8951_ePaper_Py.constants import (
    DisplayMode,
    MemoryConstants,
    PixelFormat,
    Register,
    SystemCommand,
    UserCommand,
)
from IT8951_ePaper_Py.exceptions import (
    CommunicationError,
    DeviceError,
    InitializationError,
    InvalidParameterError,
)
from IT8951_ePaper_Py.it8951 import IT8951
from IT8951_ePaper_Py.models import (
    AreaImageInfo,
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

    def test_device_info_property_none(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test device info property when info is None."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()

        # Force device_info to None
        driver._device_info = None  # type: ignore[reportPrivateUsage]

        with pytest.raises(InitializationError) as exc_info:
            _ = driver.device_info

        assert "Device info not available" in str(exc_info.value)

    def test_load_image_area_start(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test loading image area."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()

        info = LoadImageInfo(
            source_buffer=b"test",
            target_memory_addr=MemoryConstants.IMAGE_BUFFER_ADDR,
            pixel_format=PixelFormat.BPP_8,
        )

        area = AreaImageInfo(
            area_x=100,
            area_y=200,
            area_w=300,
            area_h=400,
        )

        driver.load_image_area_start(info, area)

        # Verify the command was sent
        assert mock_spi.get_last_command() == SystemCommand.LD_IMG_AREA
        buffer = mock_spi.get_data_buffer()
        # Check that area coordinates were sent
        assert 100 in buffer  # x
        assert 200 in buffer  # y
        assert 300 in buffer  # width
        assert 400 in buffer  # height

    def test_display_buffer_area(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test display buffer area operation."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()

        area = DisplayArea(
            x=52,  # Must be aligned to 4 pixels
            y=100,
            width=500,
            height=400,
            mode=DisplayMode.DU,
        )

        # Mock reading MISC register for wait_display_ready
        mock_spi.set_read_data([0])  # LUT state = 0 (ready)

        driver.display_buffer_area(area, address=0x00123456, wait=True)

        # Verify command and data
        buffer = mock_spi.get_data_buffer()
        assert 52 in buffer  # x (aligned to 4)
        assert 100 in buffer  # y
        assert 500 in buffer  # width
        assert 400 in buffer  # height
        assert 0x3456 in buffer  # address low
        assert 0x0012 in buffer  # address high

    def test_display_buffer_area_no_wait(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test display buffer area without waiting."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()

        area = DisplayArea(
            x=0,
            y=0,
            width=100,
            height=100,
        )

        driver.display_buffer_area(area, address=0, wait=False)

        # Should send command but not wait
        # The last command should be DPY_BUF_AREA
        assert mock_spi.get_last_command() == UserCommand.DPY_BUF_AREA

    def test_validate_display_area_no_device_info(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test display area validation without device info."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()

        # Force device_info to None
        driver._device_info = None  # type: ignore[reportPrivateUsage]

        area = DisplayArea(x=0, y=0, width=100, height=100)

        with pytest.raises(DeviceError) as exc_info:
            driver._validate_display_area(area)  # type: ignore[reportPrivateUsage]

        assert "Device info not available" in str(exc_info.value)

    def test_validate_display_area_exceeds_height(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test display area validation exceeding panel height."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()

        area = DisplayArea(
            x=0,
            y=500,
            width=100,
            height=300,  # 500 + 300 = 800 > 768
        )

        with pytest.raises(InvalidParameterError) as exc_info:
            driver.display_area(area)

        assert "exceeds panel height" in str(exc_info.value)

    def test_wait_display_ready_timeout(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test display ready timeout."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()

        # Mock MISC register to always return busy (bit 7 = 1)
        mock_spi.set_read_data([0x80] * 10)  # LUT state = 1 (busy)

        with pytest.raises(CommunicationError) as exc_info:
            driver._wait_display_ready(timeout_ms=100)  # type: ignore[reportPrivateUsage]

        assert "Display operation timeout after 100ms" in str(exc_info.value)

    def test_set_target_memory_addr(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test setting target memory address."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()

        driver.set_target_memory_addr(0x12345678)

        buffer = mock_spi.get_data_buffer()
        # Should write low 16 bits to LISAR
        assert Register.LISAR in buffer
        assert 0x5678 in buffer
        # Should write high 16 bits to LISAR + 2
        assert Register.LISAR + 2 in buffer
        assert 0x1234 in buffer

    def test_default_spi_interface(self) -> None:
        """Test driver creation with default SPI interface."""
        driver = IT8951()
        assert driver._spi is not None  # type: ignore[reportPrivateUsage]

    def test_load_image_write_odd_bytes(self, driver: IT8951, mock_spi: MockSPI) -> None:
        """Test loading image with odd number of bytes."""
        mock_spi.set_read_data([1024, 768, 0, 0] + [0] * 16)
        mock_spi.set_read_data([0x0000])  # REG_0204 read
        driver.init()

        # Test with odd number of bytes
        data = b"\x01\x02\x03"
        driver.load_image_write(data)

        # Should pad the last byte
        buffer = mock_spi.get_data_buffer()
        # First word: 0x01 << 8 | 0x02 = 0x0102
        assert 0x0102 in buffer
        # Second word: 0x03 << 8 | 0x00 = 0x0300 (padded)
        assert 0x0300 in buffer
