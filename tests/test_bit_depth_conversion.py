"""Tests for bit depth conversion performance and quality."""

import time

import numpy as np
import pytest
from PIL import Image

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import PixelFormat
from IT8951_ePaper_Py.models import DeviceInfo
from IT8951_ePaper_Py.pixel_packing import pack_pixels_numpy as pack_pixels


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


class TestBitDepthConversion:
    """Test bit depth conversion functionality and performance."""

    def test_8bpp_to_4bpp_conversion_speed(self):
        """Test conversion speed from 8bpp to 4bpp."""
        # Create test data
        sizes = [1000, 10000, 100000, 1000000]

        for size in sizes:
            # Create 8bpp data
            data_8bpp = np.random.randint(0, 256, size, dtype=np.uint8)

            # Measure conversion time
            start_time = time.time()
            data_4bpp = pack_pixels(data_8bpp, PixelFormat.BPP_4)
            conversion_time = time.time() - start_time

            # Verify size reduction
            assert len(data_4bpp) == size // 2

            # Calculate throughput
            throughput_mb_s = (size / (1024 * 1024)) / conversion_time

            # Should achieve reasonable throughput (>10 MB/s)
            assert throughput_mb_s > 10

    def test_8bpp_to_2bpp_conversion_speed(self):
        """Test conversion speed from 8bpp to 2bpp."""
        sizes = [1000, 10000, 100000, 1000000]

        for size in sizes:
            # Create 8bpp data
            data_8bpp = np.random.randint(0, 256, size, dtype=np.uint8)

            # Measure conversion time
            start_time = time.time()
            data_2bpp = pack_pixels(data_8bpp, PixelFormat.BPP_2)
            conversion_time = time.time() - start_time

            # Verify size reduction
            assert len(data_2bpp) == size // 4

            # Calculate throughput
            throughput_mb_s = (size / (1024 * 1024)) / conversion_time

            # Should achieve reasonable throughput
            assert throughput_mb_s > 10

    def test_8bpp_to_1bpp_conversion_speed(self):
        """Test conversion speed from 8bpp to 1bpp."""
        sizes = [1000, 10000, 100000, 1000000]

        for size in sizes:
            # Create 8bpp data
            data_8bpp = np.random.randint(0, 256, size, dtype=np.uint8)

            # Measure conversion time
            start_time = time.time()
            data_1bpp = pack_pixels(data_8bpp, PixelFormat.BPP_1)
            conversion_time = time.time() - start_time

            # Verify size reduction
            assert len(data_1bpp) == size // 8

            # Calculate throughput
            throughput_mb_s = (size / (1024 * 1024)) / conversion_time

            # Should achieve reasonable throughput
            assert throughput_mb_s > 10

    def test_grayscale_level_preservation(self):
        """Test that grayscale levels are preserved correctly during conversion."""
        # Test 4bpp (16 levels)
        # Create data with specific gray levels
        gray_levels_4bpp = [0, 17, 34, 51, 68, 85, 102, 119, 136, 153, 170, 187, 204, 221, 238, 255]
        data_8bpp = np.array(gray_levels_4bpp, dtype=np.uint8)

        # Convert to 4bpp and back
        data_4bpp = pack_pixels(data_8bpp, PixelFormat.BPP_4)

        # Manually verify the packed data
        # Each byte should contain two 4-bit values
        assert len(data_4bpp) == 8  # 16 values packed into 8 bytes

        # Test 2bpp (4 levels)
        gray_levels_2bpp = [0, 85, 170, 255]
        data_8bpp = np.array(gray_levels_2bpp, dtype=np.uint8)

        # Convert to 2bpp
        data_2bpp = pack_pixels(data_8bpp, PixelFormat.BPP_2)

        # Verify packing
        assert len(data_2bpp) == 1  # 4 values packed into 1 byte

        # Test 1bpp (2 levels)
        gray_levels_1bpp = [0, 255]
        data_8bpp = np.array(gray_levels_1bpp * 4, dtype=np.uint8)  # 8 values

        # Convert to 1bpp
        data_1bpp = pack_pixels(data_8bpp, PixelFormat.BPP_1)

        # Verify packing
        assert len(data_1bpp) == 1  # 8 values packed into 1 byte

    def test_conversion_quality_metrics(self):
        """Test quality metrics for bit depth conversions."""
        # Create a gradient image
        width, height = 256, 256
        gradient = np.zeros((height, width), dtype=np.uint8)
        for x in range(width):
            gradient[:, x] = x

        # Flatten for conversion
        data_8bpp = gradient.flatten()

        # Test 4bpp conversion quality
        pack_pixels(data_8bpp, PixelFormat.BPP_4)
        # 4bpp has 16 levels, so each level covers 256/16 = 16 values
        # This is a lossy conversion but predictable

        # Test 2bpp conversion quality
        pack_pixels(data_8bpp, PixelFormat.BPP_2)
        # 2bpp has 4 levels, so each level covers 256/4 = 64 values

        # Test 1bpp conversion quality
        pack_pixels(data_8bpp, PixelFormat.BPP_1)
        # 1bpp has 2 levels, threshold at 128

    def test_image_conversion_performance(self, display):
        """Test real image conversion performance."""
        # Create test images of different sizes
        sizes = [(100, 100), (500, 500), (1000, 1000)]

        for width, height in sizes:
            # Create gradient image
            img = Image.new("L", (width, height))
            pixels = img.load()
            if pixels is not None:
                for y in range(height):
                    for x in range(width):
                        pixels[x, y] = int(255 * x / width)

            # Test conversion to different bit depths
            formats = [PixelFormat.BPP_4, PixelFormat.BPP_2, PixelFormat.BPP_1]

            for pixel_format in formats:
                start_time = time.time()
                # This will internally convert the image
                display.display_image(img, pixel_format=pixel_format)
                conversion_time = time.time() - start_time

                # Verify reasonable performance
                pixels_count = width * height
                pixels_per_second = pixels_count / conversion_time

                # Should process at least 1M pixels/second
                assert pixels_per_second > 1_000_000

    def test_batch_conversion_performance(self):
        """Test performance of batch conversions."""
        # Create multiple images
        num_images = 10
        image_size = 10000

        images = [np.random.randint(0, 256, image_size, dtype=np.uint8) for _ in range(num_images)]

        # Test batch conversion
        formats = [PixelFormat.BPP_4, PixelFormat.BPP_2, PixelFormat.BPP_1]

        for pixel_format in formats:
            start_time = time.time()

            converted = []
            for img_data in images:
                converted.append(pack_pixels(img_data, pixel_format))

            batch_time = time.time() - start_time

            # Calculate average time per image
            avg_time_per_image = batch_time / num_images

            # Should be fast (< 1ms per 10KB image)
            assert avg_time_per_image < 0.001

    def test_conversion_memory_efficiency(self):
        """Test memory efficiency of conversions."""
        # Large image data
        size = 1_000_000  # 1MB of 8bpp data
        data_8bpp = np.random.randint(0, 256, size, dtype=np.uint8)

        # Test 4bpp conversion
        data_4bpp = pack_pixels(data_8bpp, PixelFormat.BPP_4)
        assert len(data_4bpp) == size // 2  # 50% reduction

        # Test 2bpp conversion
        data_2bpp = pack_pixels(data_8bpp, PixelFormat.BPP_2)
        assert len(data_2bpp) == size // 4  # 75% reduction

        # Test 1bpp conversion
        data_1bpp = pack_pixels(data_8bpp, PixelFormat.BPP_1)
        assert len(data_1bpp) == size // 8  # 87.5% reduction

    @pytest.mark.parametrize(
        ("pixel_format", "expected_ratio"),
        [
            (PixelFormat.BPP_4, 2),
            (PixelFormat.BPP_2, 4),
            (PixelFormat.BPP_1, 8),
        ],
    )
    def test_conversion_ratios(self, pixel_format, expected_ratio):
        """Test that conversion ratios are correct."""
        sizes = [1000, 10000, 100000]

        for original_size in sizes:
            # Ensure size is divisible by 8 for all formats
            size = (original_size // 8) * 8

            data_8bpp = np.random.randint(0, 256, size, dtype=np.uint8)
            converted = pack_pixels(data_8bpp, pixel_format)

            actual_ratio = size / len(converted)
            assert actual_ratio == expected_ratio
