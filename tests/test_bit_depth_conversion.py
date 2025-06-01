"""Tests for bit depth conversion performance and quality."""

import time

import numpy as np
import pytest
from PIL import Image
from pytest_mock import MockerFixture

from IT8951_ePaper_Py.constants import MemoryConstants, PixelFormat
from IT8951_ePaper_Py.display import EPaperDisplay
from IT8951_ePaper_Py.models import DisplayArea
from IT8951_ePaper_Py.pixel_packing import pack_pixels_numpy as pack_pixels
from IT8951_ePaper_Py.spi_interface import MockSPI


class TestBitDepthConversion:
    """Test bit depth conversion functionality and performance."""

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

    def test_8bpp_to_4bpp_conversion_speed(self):
        """Test conversion speed from 8bpp to 4bpp."""
        # Create 8-bit test images of various sizes
        test_sizes = [(100, 100), (500, 500), (1000, 1000)]

        for width, height in test_sizes:
            # Create gradient image (0-255)
            img_array = np.zeros((height, width), dtype=np.uint8)
            for i in range(height):
                img_array[i, :] = (i * 255) // height

            # Time conversion to 4bpp
            start = time.time()
            # Convert 8-bit to 4-bit by dividing by 16
            img_4bpp = (img_array >> 4).astype(np.uint8)  # 8-bit to 4-bit conversion
            packed = pack_pixels(img_4bpp, PixelFormat.BPP_4)
            conversion_time = time.time() - start

            print(f"8bpp to 4bpp conversion for {width}x{height}: {conversion_time:.4f}s")

            # Verify packed data size
            expected_size = (width * height + 1) // 2  # 2 pixels per byte
            assert len(packed) == expected_size

    def test_8bpp_to_2bpp_conversion_quality(self):
        """Test quality of conversion from 8bpp to 2bpp."""
        # Create test image with known gray levels
        width, height = 256, 256
        img_array = np.zeros((height, width), dtype=np.uint8)

        # Create 4 distinct gray levels
        img_array[:64, :] = 0  # Black
        img_array[64:128, :] = 85  # Dark gray
        img_array[128:192, :] = 170  # Light gray
        img_array[192:, :] = 255  # White

        # Convert to 2bpp (4 levels: 0, 1, 2, 3)
        img_2bpp = (img_array >> 6).astype(np.uint8)  # 8-bit to 2-bit conversion

        # Verify conversion maintains distinct levels
        assert np.all(img_2bpp[:64, :] == 0)
        assert np.all(img_2bpp[64:128, :] == 1)
        assert np.all(img_2bpp[128:192, :] == 2)
        assert np.all(img_2bpp[192:, :] == 3)

        # Pack and verify size
        packed = pack_pixels(img_2bpp, PixelFormat.BPP_2)
        expected_size = (width * height + 3) // 4  # 4 pixels per byte
        assert len(packed) == expected_size

    def test_8bpp_to_1bpp_dithering(self):
        """Test dithering quality for 1bpp conversion."""
        # Create gradient image
        width, height = 512, 512
        img = Image.new("L", (width, height))
        pixels = img.load()

        # Create horizontal gradient
        if pixels is not None:
            for y in range(height):
                for x in range(width):
                    pixels[x, y] = (x * 255) // width

        # Convert to 1bpp with dithering
        img_1bpp = img.convert("1", dither=Image.Dither.FLOYDSTEINBERG)

        # Convert to numpy array
        img_array = np.array(img_1bpp, dtype=np.uint8)

        # Verify dithering creates pattern (not all black or white)
        unique_values = np.unique(img_array)
        assert len(unique_values) == 2  # Only 0 and 1

        # Check that dithering creates reasonable distribution
        black_ratio = np.sum(img_array == 0) / img_array.size
        assert 0.3 < black_ratio < 0.7  # Should be roughly half black/white

    def test_bit_depth_memory_efficiency(self):
        """Test memory usage for different bit depths."""
        width, height = 1000, 1000
        total_pixels = width * height

        # Calculate memory usage for each format
        memory_usage = {
            PixelFormat.BPP_8: total_pixels,  # 1 byte per pixel
            PixelFormat.BPP_4: (total_pixels + 1) // 2,  # 2 pixels per byte
            PixelFormat.BPP_2: (total_pixels + 3) // 4,  # 4 pixels per byte
            PixelFormat.BPP_1: (total_pixels + 7) // 8,  # 8 pixels per byte
        }

        # Verify memory savings
        assert memory_usage[PixelFormat.BPP_4] == memory_usage[PixelFormat.BPP_8] // 2
        assert memory_usage[PixelFormat.BPP_2] == memory_usage[PixelFormat.BPP_8] // 4
        assert memory_usage[PixelFormat.BPP_1] == memory_usage[PixelFormat.BPP_8] // 8

        # Test actual packing
        for pixel_format, expected_size in memory_usage.items():
            if pixel_format == PixelFormat.BPP_8:
                continue  # 8bpp doesn't need packing

            # Create test data with appropriate bit depth
            bits_per_pixel = int(pixel_format.name.split("_")[1])
            max_value = (1 << bits_per_pixel) - 1
            test_data = np.full((height, width), max_value // 2, dtype=np.uint8)

            # Pack and verify size
            packed = pack_pixels(test_data, pixel_format)
            assert len(packed) == expected_size

    def test_conversion_performance_comparison(self):
        """Compare conversion performance across bit depths."""
        width, height = 800, 600

        # Create test image with gradient
        img_array = np.zeros((height, width), dtype=np.uint8)
        for i in range(height):
            img_array[i, :] = (i * 255) // height

        conversion_times = {}

        # Test each bit depth conversion
        for pixel_format in [PixelFormat.BPP_4, PixelFormat.BPP_2, PixelFormat.BPP_1]:
            bits_per_pixel = int(pixel_format.name.split("_")[1])

            start = time.time()

            # Convert bit depth
            if bits_per_pixel == 4:
                converted = (img_array >> 4).astype(np.uint8)
            elif bits_per_pixel == 2:
                converted = (img_array >> 6).astype(np.uint8)
            else:  # 1bpp
                converted = (img_array > 127).astype(np.uint8)

            # Pack pixels
            pack_pixels(converted, pixel_format)

            conversion_times[pixel_format] = time.time() - start

        # Print results
        for pixel_format, time_taken in conversion_times.items():
            print(f"{pixel_format.name} conversion: {time_taken:.4f}s")

    def test_partial_update_bit_depth_efficiency(self, display: EPaperDisplay):
        """Test bit depth efficiency for partial updates."""
        # This test focuses on data size calculations, not actual display

        # Test area
        area = DisplayArea(x=100, y=100, width=200, height=200)

        # Create test images for different bit depths
        test_data = {}
        data_sizes = {}

        for pixel_format in [PixelFormat.BPP_4, PixelFormat.BPP_2, PixelFormat.BPP_1]:
            # Create appropriate test pattern
            if pixel_format == PixelFormat.BPP_4:
                img = Image.new("L", (area.width, area.height), 128)
            elif pixel_format == PixelFormat.BPP_2:
                img = Image.new("L", (area.width, area.height), 170)
            else:  # 1bpp
                img = Image.new("1", (area.width, area.height), 1)

            test_data[pixel_format] = img

            # Calculate data size
            total_pixels = area.width * area.height
            if pixel_format == PixelFormat.BPP_4:
                data_sizes[pixel_format] = (total_pixels + 1) // 2
            elif pixel_format == PixelFormat.BPP_2:
                data_sizes[pixel_format] = (total_pixels + 3) // 4
            else:  # 1bpp
                data_sizes[pixel_format] = (total_pixels + 7) // 8

        # Verify size relationships
        assert data_sizes[PixelFormat.BPP_2] < data_sizes[PixelFormat.BPP_4]
        assert data_sizes[PixelFormat.BPP_1] < data_sizes[PixelFormat.BPP_2]

    def test_grayscale_preservation(self):
        """Test that grayscale values are preserved correctly during conversion."""
        width, height = 256, 256

        # Test 4bpp preservation
        # 4bpp supports 16 levels (0-15)
        for gray_4bit in range(16):
            gray_8bit = gray_4bit * 17  # Convert to 8-bit (0, 17, 34, ..., 255)
            img_array = np.full((height, width), gray_8bit, dtype=np.uint8)

            # Convert and verify
            converted = (img_array >> 4).astype(np.uint8)
            assert np.all(converted == gray_4bit)

        # Test 2bpp preservation
        # 2bpp supports 4 levels (0-3)
        for gray_2bit in range(4):
            gray_8bit = gray_2bit * 85  # Convert to 8-bit (0, 85, 170, 255)
            img_array = np.full((height, width), gray_8bit, dtype=np.uint8)

            # Convert and verify
            converted = (img_array >> 6).astype(np.uint8)
            assert np.all(converted == gray_2bit)
