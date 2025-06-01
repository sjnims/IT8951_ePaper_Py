"""Tests for alignment edge cases and performance impact."""

import time

import pytest
from PIL import Image

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.alignment import align_dimension
from IT8951_ePaper_Py.constants import PixelFormat
from IT8951_ePaper_Py.models import DeviceInfo


@pytest.fixture
def display(mocker):
    """Create display with mocked SPI."""
    # Mock SPI interface
    mock_spi = mocker.MagicMock()
    mocker.patch("IT8951_ePaper_Py.display.RaspberryPiSPI", return_value=mock_spi)

    # Create display
    display = EPaperDisplay(vcom=-2.0)

    # Mock device info
    device_info = DeviceInfo(
        panel_width=1872,
        panel_height=1404,
        memory_addr_l=0x0000,
        memory_addr_h=0x0010,
        fw_version="1.0.0",
        lut_version="M841",
    )
    mocker.patch.object(display._controller, "get_device_info", return_value=device_info)

    # Mock initialization
    mocker.patch.object(display._controller, "init")
    mocker.patch.object(display._controller, "set_vcom")

    # Initialize display
    display.init()

    return display


class TestAlignmentEdgeCases:
    """Test alignment edge cases and their performance impact."""

    def test_odd_dimension_alignment(self):
        """Test alignment with odd dimensions."""
        # Test generic alignment (4-pixel boundary)
        odd_values = [1, 3, 5, 7, 9, 11, 13, 15, 17, 99, 101, 1001]

        for value in odd_values:
            aligned = align_dimension(value)
            assert aligned % 4 == 0
            assert aligned >= value
            assert aligned - value < 4

        # Test 1bpp alignment (32-pixel boundary)
        for value in odd_values:
            aligned = align_dimension(value, PixelFormat.BPP_1)
            assert aligned % 32 == 0
            assert aligned >= value
            assert aligned - value < 32

    def test_alignment_performance_impact(self, display):
        """Test performance impact of misaligned vs aligned operations."""
        # Test cases: (width, height, description)
        test_cases = [
            (100, 100, "aligned"),
            (101, 100, "width misaligned"),
            (100, 101, "height misaligned"),
            (101, 101, "both misaligned"),
            (99, 99, "both misaligned -1"),
            (1000, 1000, "large aligned"),
            (999, 1001, "large misaligned"),
        ]

        results = {}

        for width, height, desc in test_cases:
            img = Image.new("L", (width, height), 128)

            # Measure display time
            start_time = time.time()
            display.display_image(img)
            elapsed = time.time() - start_time

            results[desc] = {
                "dimensions": (width, height),
                "time": elapsed,
                "aligned": width % 4 == 0 and height % 4 == 0,
            }

        # Compare aligned vs misaligned
        aligned_times = [r["time"] for r in results.values() if r["aligned"]]
        misaligned_times = [r["time"] for r in results.values() if not r["aligned"]]

        # Misaligned should not be significantly slower (< 20% overhead)
        if aligned_times and misaligned_times:
            avg_aligned = sum(aligned_times) / len(aligned_times)
            avg_misaligned = sum(misaligned_times) / len(misaligned_times)
            overhead = (avg_misaligned - avg_aligned) / avg_aligned
            assert overhead < 0.2

    def test_1bpp_32bit_alignment_performance(self, display):
        """Test 32-bit alignment performance for 1bpp mode."""
        # Test dimensions that are problematic for 32-bit alignment
        test_widths = [31, 32, 33, 63, 64, 65, 95, 96, 97]

        times = {}

        for width in test_widths:
            img = Image.new("L", (width, 100), 128)

            # Measure 1bpp display time
            start_time = time.time()
            display.display_image(img, pixel_format=PixelFormat.BPP_1)
            elapsed = time.time() - start_time

            times[width] = elapsed

        # Verify 32-bit aligned widths are not significantly faster
        aligned_32 = [t for w, t in times.items() if w % 32 == 0]
        misaligned_32 = [t for w, t in times.items() if w % 32 != 0]

        if aligned_32 and misaligned_32:
            avg_aligned = sum(aligned_32) / len(aligned_32)
            avg_misaligned = sum(misaligned_32) / len(misaligned_32)

            # Should handle misalignment gracefully
            assert abs(avg_aligned - avg_misaligned) / avg_aligned < 0.3

    def test_boundary_crossing_cases(self, display):
        """Test cases where image crosses alignment boundaries."""
        # Test partial updates that cross alignment boundaries
        test_cases = [
            # (x, y, width, height, description)
            (0, 0, 100, 100, "aligned start"),
            (1, 0, 100, 100, "x offset 1"),
            (3, 0, 100, 100, "x offset 3"),
            (0, 1, 100, 100, "y offset 1"),
            (3, 3, 100, 100, "xy offset 3"),
            (99, 99, 100, 100, "crossing boundary"),
            (1000, 1000, 100, 100, "far offset"),
        ]

        for x, y, width, height, _desc in test_cases:
            # Skip if out of bounds
            if x + width > display.width or y + height > display.height:
                continue

            img = Image.new("L", (width, height), 128)

            # Should handle all cases without error
            display.display_image(img, x=x, y=y)

    def test_extreme_dimensions(self, display):
        """Test extreme dimension edge cases."""
        # Very small dimensions
        small_cases = [
            (1, 1),
            (1, 10),
            (10, 1),
            (4, 4),  # Minimum aligned
        ]

        for width, height in small_cases:
            img = Image.new("L", (width, height), 128)
            # Should handle without error
            display.display_image(img)

        # Very narrow/tall dimensions
        extreme_cases = [
            (1, 1000),  # Very tall
            (1000, 1),  # Very wide
            (1872, 1),  # Full width, 1 pixel tall
            (1, 1404),  # Full height, 1 pixel wide
        ]

        for width, height in extreme_cases:
            if width <= display.width and height <= display.height:
                img = Image.new("L", (width, height), 128)
                display.display_image(img)

    def test_pixel_format_alignment_combinations(self, display):
        """Test alignment with different pixel formats."""
        # Test each pixel format with various alignments
        formats = [
            (PixelFormat.BPP_1, 32),  # 1bpp needs 32-bit alignment
            (PixelFormat.BPP_2, 4),  # 2bpp uses 4-pixel alignment
            (PixelFormat.BPP_4, 4),  # 4bpp uses 4-pixel alignment
            (PixelFormat.BPP_8, 4),  # 8bpp uses 4-pixel alignment
        ]

        misaligned_widths = [33, 65, 97, 129]  # Not aligned to 32

        for pixel_format, _expected_alignment in formats:
            for width in misaligned_widths:
                img = Image.new("L", (width, 100), 128)

                # Should handle misalignment for any format
                display.display_image(img, pixel_format=pixel_format)

    def test_alignment_with_rotation(self, display):
        """Test alignment behavior with rotation."""
        # Create a non-square, misaligned image
        img = Image.new("L", (101, 201), 128)

        # Test all rotations
        rotations = [0, 90, 180, 270]

        for rotation in rotations:
            # Rotate image
            rotated = img.rotate(rotation, expand=True) if rotation > 0 else img

            # Should handle rotated dimensions
            display.display_image(rotated)

    @pytest.mark.parametrize("offset", [0, 1, 2, 3, 4, 5, 15, 16, 31, 32])
    def test_alignment_offset_patterns(self, display, offset):
        """Test various offset patterns for alignment."""
        base_size = 96  # Divisible by 32

        # Test width offset
        img = Image.new("L", (base_size + offset, base_size), 128)
        display.display_image(img)

        # Test height offset
        img = Image.new("L", (base_size, base_size + offset), 128)
        display.display_image(img)

        # Test both offsets
        img = Image.new("L", (base_size + offset, base_size + offset), 128)
        display.display_image(img)

    def test_alignment_consistency(self):
        """Test that alignment functions are consistent."""
        # Test range of values
        for value in range(1, 200):
            # Generic alignment
            aligned_generic = align_dimension(value)

            # Should always align up to nearest 4
            assert aligned_generic >= value
            assert aligned_generic % 4 == 0
            assert aligned_generic - value < 4

            # 1bpp alignment
            aligned_1bpp = align_dimension(value, PixelFormat.BPP_1)

            # Should always align up to nearest 32
            assert aligned_1bpp >= value
            assert aligned_1bpp % 32 == 0
            assert aligned_1bpp - value < 32

            # 1bpp should be more restrictive
            assert aligned_1bpp >= aligned_generic
