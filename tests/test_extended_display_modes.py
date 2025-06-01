"""Tests for extended display modes (GLR16, GLD16, DU4)."""

from typing import cast
from unittest.mock import MagicMock

import pytest
from PIL import Image
from pytest_mock import MockerFixture

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode, DisplayModeCharacteristics, PixelFormat
from IT8951_ePaper_Py.models import DeviceInfo, DisplayArea


@pytest.fixture
def mock_display(mocker: MockerFixture) -> EPaperDisplay:
    """Create a mock display for testing."""
    # Mock SPI interface
    mock_spi = mocker.patch("IT8951_ePaper_Py.display.create_spi_interface")
    mock_spi_instance = MagicMock()
    mock_spi.return_value = mock_spi_instance

    # Create display
    display = EPaperDisplay(vcom=-2.0)

    # Mock device info
    device_info = DeviceInfo(
        panel_width=1872,
        panel_height=1404,
        memory_addr_l=0x36E0,
        memory_addr_h=0x0012,
        fw_version="1.0",
        lut_version="1.0",
    )
    display._controller._device_info = device_info
    display._width = device_info.panel_width
    display._height = device_info.panel_height
    display._initialized = True

    # Mock controller methods
    display._controller.display_area = MagicMock()
    display._controller.pack_pixels = MagicMock(return_value=b"packed_data")
    display._controller.load_image_area_start = MagicMock()
    display._controller.load_image_write = MagicMock()
    display._controller.load_image_end = MagicMock()

    return display


class TestExtendedDisplayModes:
    """Test extended display mode functionality."""

    def test_mode_characteristics_defined(self):
        """Test that all extended modes have characteristics defined."""
        extended_modes = [DisplayMode.GLR16, DisplayMode.GLD16, DisplayMode.DU4]

        for mode in extended_modes:
            assert mode in DisplayModeCharacteristics.MODE_INFO
            mode_info = DisplayModeCharacteristics.MODE_INFO[mode]

            # Check required fields
            assert "name" in mode_info
            assert "grayscale_levels" in mode_info
            assert "speed" in mode_info
            assert "quality" in mode_info
            assert "use_case" in mode_info
            assert "ghosting" in mode_info
            assert "recommended_bpp" in mode_info

    def test_glr16_mode(self, mock_display: EPaperDisplay):
        """Test GLR16 (Ghost Reduction) mode."""
        # Create test image
        img = Image.new("L", (100, 100), 128)

        # Display with GLR16 mode
        mock_display.display_image(img, mode=DisplayMode.GLR16)

        # Verify display_area was called with correct mode
        controller = mock_display._controller
        display_area_mock = cast(MagicMock, controller.display_area)
        display_area_mock.assert_called_once()
        call_args = display_area_mock.call_args[0][0]
        assert isinstance(call_args, DisplayArea)
        assert call_args.mode == DisplayMode.GLR16

    def test_gld16_mode(self, mock_display: EPaperDisplay):
        """Test GLD16 (Ghost Level Detection) mode."""
        # Create test image
        img = Image.new("L", (100, 100), 64)

        # Display with GLD16 mode
        mock_display.display_image(img, mode=DisplayMode.GLD16)

        # Verify display_area was called with correct mode
        controller = mock_display._controller
        display_area_mock = cast(MagicMock, controller.display_area)
        display_area_mock.assert_called_once()
        call_args = display_area_mock.call_args[0][0]
        assert isinstance(call_args, DisplayArea)
        assert call_args.mode == DisplayMode.GLD16

    def test_du4_mode(self, mock_display: EPaperDisplay):
        """Test DU4 (Direct Update 4-level) mode."""
        # Create test image with 4 gray levels
        img = Image.new("L", (100, 100))
        # Create 4 distinct gray levels using putpixel
        for y in range(100):
            for x in range(100):
                if x < 25:
                    img.putpixel((x, y), 0)
                elif x < 50:
                    img.putpixel((x, y), 85)
                elif x < 75:
                    img.putpixel((x, y), 170)
                else:
                    img.putpixel((x, y), 255)

        # Display with DU4 mode and appropriate pixel format
        mock_display.display_image(img, mode=DisplayMode.DU4, pixel_format=PixelFormat.BPP_2)

        # Verify display_area was called with correct mode
        controller = mock_display._controller
        display_area_mock = cast(MagicMock, controller.display_area)
        display_area_mock.assert_called_once()
        call_args = display_area_mock.call_args[0][0]
        assert isinstance(call_args, DisplayArea)
        assert call_args.mode == DisplayMode.DU4

    def test_mode_pixel_format_validation_warnings(
        self, mock_display: EPaperDisplay, mocker: MockerFixture
    ):
        """Test that warnings are issued for non-optimal pixel format combinations."""
        mock_warn = mocker.patch("warnings.warn")

        # Create test image aligned to avoid alignment warnings
        img = Image.new("L", (128, 128), 128)

        # Test GLR16 with non-recommended pixel format (1bpp)
        mock_display.display_image(img, mode=DisplayMode.GLR16, pixel_format=PixelFormat.BPP_1)

        # Check that we got the pixel format warning
        pixel_format_warnings = [
            call for call in mock_warn.call_args_list if "works best with" in str(call[0][0])
        ]
        assert len(pixel_format_warnings) >= 1
        warning_message = str(pixel_format_warnings[0][0][0])
        assert "GLR16" in warning_message
        assert "works best with" in warning_message
        assert "1bpp was selected" in warning_message  # PixelFormat.BPP_1 means 1 bit per pixel

    def test_hardware_support_warning(self, mock_display: EPaperDisplay, mocker: MockerFixture):
        """Test that hardware support warnings are issued for extended modes."""
        mock_warn = mocker.patch("warnings.warn")

        # Create test image
        img = Image.new("L", (100, 100), 128)

        # Test each extended mode
        extended_modes = [DisplayMode.GLR16, DisplayMode.GLD16, DisplayMode.DU4]

        for mode in extended_modes:
            mock_warn.reset_mock()
            mock_display.display_image(img, mode=mode)

            # Check hardware support warning was issued
            warning_calls = [
                call for call in mock_warn.call_args_list if "extended mode" in str(call[0][0])
            ]
            assert len(warning_calls) == 1
            warning_message = str(warning_calls[0][0][0])
            assert "may not be supported" in warning_message

    def test_du4_with_2bpp_format(self, mock_display: EPaperDisplay):
        """Test DU4 mode with recommended 2bpp pixel format."""
        # Create test image
        img = Image.new("L", (100, 100), 128)

        # Display with DU4 and 2bpp (no warning expected)
        with pytest.warns(UserWarning, match="extended mode"):
            # Only hardware support warning, not pixel format warning
            mock_display.display_image(img, mode=DisplayMode.DU4, pixel_format=PixelFormat.BPP_2)

        # Verify correct packing was used
        controller = mock_display._controller
        pack_pixels_mock = cast(MagicMock, controller.pack_pixels)
        pack_pixels_mock.assert_called_with(img.tobytes(), PixelFormat.BPP_2)

    def test_mode_value_consistency(self):
        """Test that mode values match expected constants."""
        assert DisplayMode.GLR16.value == 5
        assert DisplayMode.GLD16.value == 6
        assert DisplayMode.DU4.value == 7

    def test_partial_update_with_extended_modes(self, mock_display: EPaperDisplay):
        """Test partial updates work with extended modes."""
        # Create small test image
        img = Image.new("L", (50, 50), 200)

        # Test partial update with each extended mode
        for mode in [DisplayMode.GLR16, DisplayMode.GLD16, DisplayMode.DU4]:
            display_area_mock = cast(MagicMock, mock_display._controller.display_area)
            display_area_mock.reset_mock()
            mock_display.display_partial(img, x=100, y=100, mode=mode)

            # Verify mode was passed correctly
            controller = mock_display._controller
            display_area_mock = cast(MagicMock, controller.display_area)
            display_area_mock.assert_called_once()
            call_args = display_area_mock.call_args[0][0]
            assert call_args.mode == mode

    def test_mode_characteristics_access(self):
        """Test accessing mode characteristics programmatically."""
        # Get DU4 characteristics
        du4_info = DisplayModeCharacteristics.MODE_INFO[DisplayMode.DU4]

        assert du4_info["grayscale_levels"] == 4
        assert du4_info["speed"] == "fast"
        assert du4_info["quality"] == "medium"
        recommended_bpp = du4_info["recommended_bpp"]
        assert isinstance(recommended_bpp, list)
        assert 1 in recommended_bpp  # 2bpp
        assert 2 in recommended_bpp  # 4bpp

    def test_all_modes_have_characteristics(self):
        """Test that all DisplayMode enum values have characteristics defined."""
        for mode in DisplayMode:
            assert mode in DisplayModeCharacteristics.MODE_INFO
            mode_info = DisplayModeCharacteristics.MODE_INFO[mode]
            assert isinstance(mode_info, dict)
            assert len(mode_info) > 0
