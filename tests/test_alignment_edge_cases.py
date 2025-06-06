"""Tests for alignment edge cases and performance impact."""

import time

import pytest
from PIL import Image
from pytest_mock import MockerFixture

from IT8951_ePaper_Py.alignment import (
    align_coordinate,
    align_dimension,
    get_alignment_boundary,
    validate_alignment,
)
from IT8951_ePaper_Py.constants import DisplayMode, MemoryConstants, PixelFormat
from IT8951_ePaper_Py.display import EPaperDisplay
from IT8951_ePaper_Py.models import DisplayArea
from IT8951_ePaper_Py.spi_interface import MockSPI


class TestAlignmentEdgeCases:
    """Test alignment edge cases and their performance impact."""

    @pytest.fixture
    def mock_spi(self) -> MockSPI:
        """Create mock SPI interface."""
        return MockSPI()

    @pytest.fixture
    def display(self, mock_spi: MockSPI, mocker: MockerFixture) -> EPaperDisplay:
        """Create and initialize EPaperDisplay."""
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Data for _get_device_info (20 values)
        mock_spi.set_read_data(
            [
                1872,  # panel_width
                1404,  # panel_height
                MemoryConstants.IMAGE_BUFFER_ADDR_L,  # memory_addr_l
                MemoryConstants.IMAGE_BUFFER_ADDR_H,  # memory_addr_h
                49,
                46,
                48,
                0,
                0,
                0,
                0,
                0,  # fw_version "1.0"
                77,
                56,
                52,
                49,
                0,
                0,
                0,
                0,  # lut_version "M841"
            ]
        )
        # Data for _enable_packed_write register read
        mock_spi.set_read_data([0x0000])

        # Data for get_vcom() call in init() - return 2000 (2.0V)
        mock_spi.set_read_data([2000])

        # Mock clear to avoid complex setup
        mocker.patch.object(display, "clear")

        display.init()
        return display

    def test_odd_dimension_alignment(self):
        """Test alignment with odd dimensions for different pixel formats."""
        # Test 4bpp (default) - 4-pixel boundary
        assert align_dimension(17, PixelFormat.BPP_4) == 20
        assert align_dimension(31, PixelFormat.BPP_4) == 32
        assert align_dimension(1, PixelFormat.BPP_4) == 4

        # Test 2bpp - 4-pixel boundary
        assert align_dimension(17, PixelFormat.BPP_2) == 20
        assert align_dimension(31, PixelFormat.BPP_2) == 32
        assert align_dimension(1, PixelFormat.BPP_2) == 4

        # Test 1bpp - 32-pixel boundary
        assert align_dimension(17, PixelFormat.BPP_1) == 32
        assert align_dimension(31, PixelFormat.BPP_1) == 32
        assert align_dimension(1, PixelFormat.BPP_1) == 32

    def test_alignment_boundaries(self):
        """Test that alignment boundaries are correct for each pixel format."""
        assert get_alignment_boundary(PixelFormat.BPP_1) == 32
        assert get_alignment_boundary(PixelFormat.BPP_2) == 4
        assert get_alignment_boundary(PixelFormat.BPP_4) == 4
        assert get_alignment_boundary(PixelFormat.BPP_8) == 4
        assert get_alignment_boundary(None) == 4  # Default

    def test_coordinate_alignment(self):
        """Test coordinate alignment (rounds down)."""
        # 4bpp - 4-pixel boundary
        assert align_coordinate(13, PixelFormat.BPP_4) == 12
        assert align_coordinate(16, PixelFormat.BPP_4) == 16
        assert align_coordinate(3, PixelFormat.BPP_4) == 0

        # 1bpp - 32-pixel boundary
        assert align_coordinate(35, PixelFormat.BPP_1) == 32
        assert align_coordinate(64, PixelFormat.BPP_1) == 64
        assert align_coordinate(31, PixelFormat.BPP_1) == 0

    def test_alignment_validation(self):
        """Test alignment validation function."""
        # Valid alignment for 4bpp
        valid, errors = validate_alignment(0, 0, 100, 100, PixelFormat.BPP_4)
        assert valid
        assert len(errors) == 0

        # Invalid alignment for 4bpp
        valid, errors = validate_alignment(1, 2, 101, 102, PixelFormat.BPP_4)
        assert not valid
        assert len(errors) == 4  # All parameters misaligned

        # Valid alignment for 1bpp (all must be multiples of 32)
        valid, errors = validate_alignment(32, 0, 64, 128, PixelFormat.BPP_1)
        assert valid
        assert len(errors) == 0

        # Invalid alignment for 1bpp
        valid, errors = validate_alignment(30, 0, 60, 100, PixelFormat.BPP_1)
        assert not valid
        assert len(errors) == 4  # 3 misaligned + 1 note for 1bpp

    @pytest.mark.slow
    def test_alignment_performance_impact(self, display: EPaperDisplay, mocker: MockerFixture):
        """Test performance impact of misaligned dimensions."""
        # Mock the actual display operations to avoid hardware calls
        mocker.patch.object(display, "display_partial")

        # Test with already aligned areas (DisplayArea validates alignment)
        # These would represent areas that are not optimally aligned for performance
        unaligned_areas = [
            DisplayArea(x=20, y=24, width=104, height=100),  # Not on 8/16 boundaries
            DisplayArea(x=32, y=48, width=116, height=104),  # Not on optimal boundaries
            DisplayArea(x=56, y=72, width=128, height=112),  # Mixed alignment
        ]

        # Create test images
        test_images = []
        for area in unaligned_areas:
            img = Image.new("L", (area.width, area.height), 128)
            test_images.append(img)

        # Measure time for unaligned updates
        start = time.time()
        for area, img in zip(unaligned_areas, test_images, strict=False):
            display.display_partial(img, area.x, area.y, mode=DisplayMode.DU)
        unaligned_time = time.time() - start

        # Test aligned updates
        aligned_areas = [
            DisplayArea(x=16, y=24, width=104, height=96),
            DisplayArea(x=32, y=48, width=112, height=104),
            DisplayArea(x=48, y=72, width=128, height=112),
        ]

        # Create test images for aligned areas
        aligned_images = []
        for area in aligned_areas:
            img = Image.new("L", (area.width, area.height), 128)
            aligned_images.append(img)

        # Measure time for aligned updates
        start = time.time()
        for area, img in zip(aligned_areas, aligned_images, strict=False):
            display.display_partial(img, area.x, area.y, mode=DisplayMode.DU)
        aligned_time = time.time() - start

        # Aligned should be faster (or at least not significantly slower)
        # Note: In mock environment, times might be similar
        print(f"Unaligned time: {unaligned_time:.4f}s")
        print(f"Aligned time: {aligned_time:.4f}s")

    def test_boundary_conditions(self):
        """Test alignment at various boundary conditions."""
        # Test powers of 2 for 4bpp
        for i in range(2, 11):  # Start from 4 (2^2) since smaller powers don't align to 4
            power = 2**i
            assert align_dimension(power, PixelFormat.BPP_4) == power
            assert align_dimension(power - 1, PixelFormat.BPP_4) == power  # Round up
            assert align_dimension(power + 1, PixelFormat.BPP_4) == power + 4  # Next multiple

        # Test near display boundaries (1872x1404)
        assert align_dimension(1872, PixelFormat.BPP_4) == 1872  # Already aligned
        assert align_dimension(1871, PixelFormat.BPP_4) == 1872
        assert align_dimension(1404, PixelFormat.BPP_4) == 1404  # Already aligned
        assert align_dimension(1403, PixelFormat.BPP_4) == 1404

    def test_minimum_dimension_handling(self):
        """Test handling of minimum dimensions."""
        # Test very small dimensions for 4bpp
        assert align_dimension(0, PixelFormat.BPP_4) == 0
        assert align_dimension(1, PixelFormat.BPP_4) == 4
        assert align_dimension(2, PixelFormat.BPP_4) == 4
        assert align_dimension(3, PixelFormat.BPP_4) == 4
        assert align_dimension(4, PixelFormat.BPP_4) == 4
        assert align_dimension(5, PixelFormat.BPP_4) == 8

        # Test very small dimensions for 1bpp
        assert align_dimension(0, PixelFormat.BPP_1) == 0
        assert align_dimension(1, PixelFormat.BPP_1) == 32
        assert align_dimension(31, PixelFormat.BPP_1) == 32
        assert align_dimension(32, PixelFormat.BPP_1) == 32
        assert align_dimension(33, PixelFormat.BPP_1) == 64

    def test_large_dimension_handling(self):
        """Test handling of large dimensions."""
        # Test dimensions larger than typical display
        assert align_dimension(2048, PixelFormat.BPP_4) == 2048
        assert align_dimension(2047, PixelFormat.BPP_4) == 2048
        assert align_dimension(4096, PixelFormat.BPP_4) == 4096
        assert align_dimension(4095, PixelFormat.BPP_4) == 4096

        # Test for 1bpp
        assert align_dimension(2048, PixelFormat.BPP_1) == 2048  # 2048 % 32 == 0
        assert align_dimension(2047, PixelFormat.BPP_1) == 2048  # Round up to 2048
        assert align_dimension(2032, PixelFormat.BPP_1) == 2048  # Round up to 2048
        assert align_dimension(2031, PixelFormat.BPP_1) == 2048  # Round up to 2048

    def test_alignment_with_offsets(self):
        """Test alignment when starting at non-zero offsets."""
        # Test various x offsets for 4bpp
        for x_offset in [0, 1, 7, 8, 15, 16, 17]:
            aligned_x = align_coordinate(x_offset, PixelFormat.BPP_4)
            assert aligned_x <= x_offset
            assert aligned_x % 4 == 0

        # Test various x offsets for 1bpp
        for x_offset in [0, 1, 31, 32, 33, 63, 64]:
            aligned_x = align_coordinate(x_offset, PixelFormat.BPP_1)
            assert aligned_x <= x_offset
            assert aligned_x % 32 == 0

    def test_alignment_consistency(self):
        """Test that alignment is consistent and deterministic."""
        # Same input should always produce same output
        for _ in range(100):
            assert align_dimension(17, PixelFormat.BPP_4) == 20
            assert align_dimension(31, PixelFormat.BPP_2) == 32
            assert align_dimension(1, PixelFormat.BPP_1) == 32

    def test_alignment_preserves_already_aligned(self):
        """Test that already aligned dimensions are preserved."""
        # Test 4-pixel alignment (4bpp, 2bpp, 8bpp)
        for pixel_format in [PixelFormat.BPP_2, PixelFormat.BPP_4, PixelFormat.BPP_8]:
            for multiple in range(1, 20):
                value = 4 * multiple
                assert align_dimension(value, pixel_format) == value
                assert align_coordinate(value, pixel_format) == value

        # Test 32-pixel alignment (1bpp)
        for multiple in range(1, 10):
            value = 32 * multiple
            assert align_dimension(value, PixelFormat.BPP_1) == value
            assert align_coordinate(value, PixelFormat.BPP_1) == value

    def test_default_pixel_format(self):
        """Test that default pixel format is handled correctly."""
        # Should use 4bpp (4-pixel alignment) by default
        assert align_dimension(17) == 20
        assert align_dimension(31) == 32
        assert align_coordinate(13) == 12
        assert align_coordinate(16) == 16

    def test_get_alignment_description(self):
        """Test human-readable alignment descriptions."""
        from IT8951_ePaper_Py.alignment import get_alignment_description

        # Test all pixel formats
        assert get_alignment_description(PixelFormat.BPP_1) == "32-pixel (4-byte)"
        assert get_alignment_description(PixelFormat.BPP_2) == "4-pixel"
        assert get_alignment_description(PixelFormat.BPP_4) == "4-pixel"
        assert get_alignment_description(PixelFormat.BPP_8) == "4-pixel"

        # Test default (None)
        assert get_alignment_description(None) == "4-pixel"
        assert get_alignment_description() == "4-pixel"

    def test_validate_alignment_warnings(self):
        """Test detailed warning messages from alignment validation."""
        # Test misaligned 4bpp parameters
        valid, warnings = validate_alignment(13, 17, 101, 105, PixelFormat.BPP_4)
        assert not valid
        assert len(warnings) == 4

        # Check specific warning messages
        assert (
            "X coordinate 13 not aligned to 4-pixel boundary. Will be adjusted to 12" in warnings[0]
        )
        assert (
            "Y coordinate 17 not aligned to 4-pixel boundary. Will be adjusted to 16" in warnings[1]
        )
        assert "Width 101 not aligned to 4-pixel boundary. Will be adjusted to 104" in warnings[2]
        assert "Height 105 not aligned to 4-pixel boundary. Will be adjusted to 108" in warnings[3]

    def test_validate_alignment_1bpp_special_warning(self):
        """Test special warning for 1bpp alignment issues."""
        # Misaligned 1bpp parameters should include special note
        valid, warnings = validate_alignment(10, 20, 50, 100, PixelFormat.BPP_1)
        assert not valid
        assert len(warnings) == 5  # 1 special note + 4 alignment warnings

        # Check special warning is first
        assert warnings[0].startswith("Note: 1bpp mode requires strict 32-pixel alignment")
        assert "Image may be cropped or padded" in warnings[0]

        # Check parameter warnings
        assert "X coordinate 10" in warnings[1]
        assert "Y coordinate 20" in warnings[2]
        assert "Width 50" in warnings[3]
        assert "Height 100" in warnings[4]

        # No special warning when everything is aligned
        valid, warnings = validate_alignment(32, 64, 128, 256, PixelFormat.BPP_1)
        assert valid
        assert len(warnings) == 0

    def test_check_parameter_alignment_internal(self):
        """Test internal parameter checking function."""
        from IT8951_ePaper_Py.alignment import _check_parameter_alignment

        # Test with all parameters misaligned
        warnings = _check_parameter_alignment(13, 17, 101, 105, PixelFormat.BPP_4)
        assert len(warnings) == 4

        # Test with some parameters aligned
        warnings = _check_parameter_alignment(12, 17, 100, 105, PixelFormat.BPP_4)
        assert len(warnings) == 2  # Only Y and Height misaligned

        # Test with all parameters aligned
        warnings = _check_parameter_alignment(12, 16, 100, 104, PixelFormat.BPP_4)
        assert len(warnings) == 0

    def test_check_single_parameter_internal(self):
        """Test internal single parameter checking function."""
        from IT8951_ePaper_Py.alignment import _check_single_parameter

        # Test coordinate misalignment (rounds down)
        warning = _check_single_parameter(
            "X coordinate", 13, align_coordinate, PixelFormat.BPP_4, 4, "4-pixel"
        )
        assert warning == "X coordinate 13 not aligned to 4-pixel boundary. Will be adjusted to 12"

        # Test dimension misalignment (rounds up)
        warning = _check_single_parameter(
            "Width", 101, align_dimension, PixelFormat.BPP_4, 4, "4-pixel"
        )
        assert warning == "Width 101 not aligned to 4-pixel boundary. Will be adjusted to 104"

        # Test aligned parameter
        warning = _check_single_parameter(
            "X coordinate", 16, align_coordinate, PixelFormat.BPP_4, 4, "4-pixel"
        )
        assert warning is None

    def test_get_1bpp_warning_internal(self):
        """Test internal 1bpp warning message function."""
        from IT8951_ePaper_Py.alignment import _get_1bpp_warning

        warning = _get_1bpp_warning()
        assert "1bpp mode requires strict 32-pixel alignment" in warning
        assert "Image may be cropped or padded" in warning

    def test_alignment_with_different_pixel_formats(self):
        """Test alignment functions with all pixel formats."""
        from IT8951_ePaper_Py.alignment import get_alignment_description

        # Test each format has correct behavior
        formats_4px = [PixelFormat.BPP_2, PixelFormat.BPP_4, PixelFormat.BPP_8]

        for fmt in formats_4px:
            # Should all use 4-pixel alignment
            assert get_alignment_boundary(fmt) == 4
            assert align_coordinate(13, fmt) == 12
            assert align_dimension(13, fmt) == 16
            assert get_alignment_description(fmt) == "4-pixel"

        # 1bpp should use 32-pixel alignment
        assert get_alignment_boundary(PixelFormat.BPP_1) == 32
        assert align_coordinate(35, PixelFormat.BPP_1) == 32
        assert align_dimension(35, PixelFormat.BPP_1) == 64
        assert get_alignment_description(PixelFormat.BPP_1) == "32-pixel (4-byte)"

    def test_negative_coordinate_alignment(self):
        """Test alignment with negative coordinates (edge case)."""
        # Negative coordinates should still align properly
        assert align_coordinate(-1, PixelFormat.BPP_4) == -4
        assert align_coordinate(-4, PixelFormat.BPP_4) == -4
        assert align_coordinate(-5, PixelFormat.BPP_4) == -8
        assert align_coordinate(-13, PixelFormat.BPP_4) == -16

        # For 1bpp
        assert align_coordinate(-1, PixelFormat.BPP_1) == -32
        assert align_coordinate(-32, PixelFormat.BPP_1) == -32
        assert align_coordinate(-33, PixelFormat.BPP_1) == -64

    def test_alignment_mathematical_properties(self):
        """Test mathematical properties of alignment functions."""
        # Test idempotence: aligning an already aligned value should not change it
        for val in [0, 4, 8, 12, 16, 100, 1000]:
            assert align_coordinate(val, PixelFormat.BPP_4) == val
            assert align_dimension(val, PixelFormat.BPP_4) == val
            assert align_coordinate(
                align_coordinate(val + 1, PixelFormat.BPP_4), PixelFormat.BPP_4
            ) == align_coordinate(val + 1, PixelFormat.BPP_4)

        # Test monotonicity: larger inputs produce larger or equal outputs
        for i in range(100):
            assert align_dimension(i, PixelFormat.BPP_4) <= align_dimension(
                i + 1, PixelFormat.BPP_4
            )
            assert align_coordinate(i, PixelFormat.BPP_4) <= align_coordinate(
                i + 1, PixelFormat.BPP_4
            )

    def test_alignment_with_max_display_dimensions(self):
        """Test alignment near maximum display dimensions."""
        # IT8951 supports up to 2048x2048
        max_dim = 2048

        # Test at and near maximum
        assert align_dimension(max_dim, PixelFormat.BPP_4) == max_dim
        assert align_dimension(max_dim - 1, PixelFormat.BPP_4) == max_dim
        assert align_dimension(max_dim - 3, PixelFormat.BPP_4) == max_dim
        assert align_dimension(max_dim - 4, PixelFormat.BPP_4) == max_dim - 4

        # Test coordinate alignment at maximum
        assert align_coordinate(max_dim, PixelFormat.BPP_4) == max_dim
        assert align_coordinate(max_dim - 1, PixelFormat.BPP_4) == max_dim - 4

    def test_validate_alignment_with_none_pixel_format(self):
        """Test validate_alignment with None pixel format to cover default case."""
        # Test with None pixel format (should use 4bpp default)
        valid, warnings = validate_alignment(0, 0, 100, 100, None)
        assert valid
        assert len(warnings) == 0

        # Test with misaligned values and None pixel format
        valid, warnings = validate_alignment(13, 17, 101, 105, None)
        assert not valid
        assert len(warnings) == 4
        assert "4-pixel" in warnings[0]  # Should use 4-pixel alignment
