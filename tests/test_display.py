"""Tests for high-level display interface."""

import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from pytest_mock import MockerFixture

from IT8951_ePaper_Py.constants import DisplayMode, Rotation
from IT8951_ePaper_Py.display import EPaperDisplay
from IT8951_ePaper_Py.exceptions import DisplayError, InvalidParameterError
from IT8951_ePaper_Py.spi_interface import MockSPI


class TestEPaperDisplay:
    """Test EPaperDisplay class."""

    @pytest.fixture
    def mock_spi(self) -> MockSPI:
        """Create mock SPI interface."""
        return MockSPI()

    @pytest.fixture
    def display(self, mock_spi: MockSPI) -> EPaperDisplay:
        """Create EPaperDisplay with mock SPI."""
        return EPaperDisplay(spi_interface=mock_spi)

    @pytest.fixture
    def initialized_display(
        self, display: EPaperDisplay, mock_spi: MockSPI, mocker: MockerFixture
    ) -> EPaperDisplay:
        """Create and initialize EPaperDisplay."""
        # Data for _get_device_info (20 values)
        mock_spi.set_read_data([1024, 768, 0x36E0, 0x0012] + [0] * 16)
        # Data for _enable_packed_write register read
        mock_spi.set_read_data([0x0000])

        # Mock clear to avoid complex setup
        mocker.patch.object(display, "clear")

        display.init()
        return display

    def test_init(self, display: EPaperDisplay, mock_spi: MockSPI, mocker: MockerFixture) -> None:
        """Test display initialization."""
        # Data for _get_device_info (20 values)
        mock_spi.set_read_data([1024, 768, 0x36E0, 0x0012] + [0] * 16)
        # Data for _enable_packed_write register read
        mock_spi.set_read_data([0x0000])

        # Mock clear to avoid complex setup
        mocker.patch.object(display, "clear")

        width, height = display.init()

        assert width == 1024
        assert height == 768
        assert display._initialized  # type: ignore[reportPrivateUsage]

        width2, height2 = display.init()
        assert (width2, height2) == (width, height)

    def test_close(self, initialized_display: EPaperDisplay) -> None:
        """Test display close."""
        initialized_display.close()
        assert not initialized_display._initialized  # type: ignore[reportPrivateUsage]

    def test_clear(self, initialized_display: EPaperDisplay, mock_spi: MockSPI) -> None:
        """Test display clear."""
        mock_spi.set_read_data([0])
        initialized_display.clear()

        buffer = mock_spi.get_data_buffer()

        assert any(len(chunk) > 0 for chunk in [buffer])

        initialized_display.clear(color=0x00)

    def test_display_image_from_pil(
        self, initialized_display: EPaperDisplay, mock_spi: MockSPI
    ) -> None:
        """Test displaying PIL image."""
        img = Image.new("L", (800, 600), color=128)
        mock_spi.set_read_data([0])

        initialized_display.display_image(img, x=0, y=0, mode=DisplayMode.GC16)

        buffer = mock_spi.get_data_buffer()
        assert len(buffer) > 0

    def test_display_image_from_file(
        self, initialized_display: EPaperDisplay, mock_spi: MockSPI, tmp_path: Path
    ) -> None:
        """Test displaying image from file."""
        img = Image.new("L", (100, 100), color=255)
        img_path = tmp_path / "test.png"
        img.save(img_path)

        mock_spi.set_read_data([0])
        initialized_display.display_image(img_path, x=0, y=0)

    def test_display_image_from_bytes(
        self, initialized_display: EPaperDisplay, mock_spi: MockSPI
    ) -> None:
        """Test displaying image from bytes buffer."""
        img = Image.new("L", (100, 100), color=0)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        mock_spi.set_read_data([0])
        initialized_display.display_image(buffer, x=0, y=0)

    def test_display_image_validation(self, initialized_display: EPaperDisplay) -> None:
        """Test image display validation."""
        img = Image.new("L", (2000, 100))

        with pytest.raises(InvalidParameterError) as exc_info:
            initialized_display.display_image(img, x=0, y=0)

        assert "exceeds display width" in str(exc_info.value)

        img = Image.new("L", (100, 1000))
        with pytest.raises(InvalidParameterError) as exc_info:
            initialized_display.display_image(img, x=0, y=700)

        assert "exceeds display height" in str(exc_info.value)

    def test_display_image_rotation(
        self, initialized_display: EPaperDisplay, mock_spi: MockSPI
    ) -> None:
        """Test image rotation."""
        img = Image.new("L", (200, 100), color=64)
        mock_spi.set_read_data([0])

        initialized_display.display_image(img, rotation=Rotation.ROTATE_90)

        img2 = Image.new("L", (100, 200), color=64)
        mock_spi.set_read_data([0])
        initialized_display.display_image(img2, rotation=Rotation.ROTATE_180)

    def test_display_partial(self, initialized_display: EPaperDisplay, mock_spi: MockSPI) -> None:
        """Test partial display update."""
        img = Image.new("L", (100, 100), color=200)
        mock_spi.set_read_data([0])

        initialized_display.display_partial(img, x=100, y=100, mode=DisplayMode.DU)

        arr = (np.ones((100, 100), dtype=np.uint8) * 128).astype(np.uint8)
        mock_spi.set_read_data([0])
        initialized_display.display_partial(arr, x=200, y=200)

        arr_float = np.ones((100, 100), dtype=np.float32) * 0.5
        mock_spi.set_read_data([0])
        initialized_display.display_partial(arr_float, x=300, y=300)  # type: ignore[arg-type]

    def test_vcom_operations(self, initialized_display: EPaperDisplay, mock_spi: MockSPI) -> None:
        """Test VCOM operations."""
        initialized_display.set_vcom(-3.0)

        mock_spi.set_read_data([3000])
        voltage = initialized_display.get_vcom()
        assert voltage == -3.0

    def test_power_operations(self, initialized_display: EPaperDisplay) -> None:
        """Test power operations."""
        initialized_display.sleep()
        initialized_display.standby()

    def test_properties(self, initialized_display: EPaperDisplay) -> None:
        """Test display properties."""
        assert initialized_display.width == 1024
        assert initialized_display.height == 768
        assert initialized_display.size == (1024, 768)

    def test_properties_without_init(self, display: EPaperDisplay) -> None:
        """Test properties raise error without initialization."""
        with pytest.raises(DisplayError):
            _ = display.width

        with pytest.raises(DisplayError):
            _ = display.height

        with pytest.raises(DisplayError):
            _ = display.size

    def test_operations_without_init(self, display: EPaperDisplay) -> None:
        """Test operations fail without initialization."""
        with pytest.raises(DisplayError):
            display.clear()

        with pytest.raises(DisplayError):
            display.display_image(Image.new("L", (100, 100)))

        with pytest.raises(DisplayError):
            display.set_vcom(-2.0)

    def test_image_alignment(self, initialized_display: EPaperDisplay, mock_spi: MockSPI) -> None:
        """Test image coordinate and dimension alignment."""
        img = Image.new("L", (99, 99), color=128)
        mock_spi.set_read_data([0])

        initialized_display.display_image(img, x=1, y=2)

        buffer = mock_spi.get_data_buffer()
        assert 0 in buffer
        assert 100 in buffer

    def test_invalid_image_source(self, initialized_display: EPaperDisplay) -> None:
        """Test invalid image source handling."""
        with pytest.raises(InvalidParameterError) as exc_info:
            initialized_display.display_image(12345)  # type: ignore[arg-type]

        assert "Invalid image source" in str(exc_info.value)

    def test_rgb_to_grayscale_conversion(
        self, initialized_display: EPaperDisplay, mock_spi: MockSPI
    ) -> None:
        """Test RGB image is converted to grayscale."""
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        mock_spi.set_read_data([0])

        initialized_display.display_image(img)

        assert mock_spi.get_data_buffer()
