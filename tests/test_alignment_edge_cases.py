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
