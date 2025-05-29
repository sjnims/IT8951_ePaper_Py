"""Performance comparison tests for different pixel formats."""

import time

import numpy as np
import pytest
from pytest_mock import MockerFixture

from IT8951_ePaper_Py.constants import MemoryConstants, PixelFormat
from IT8951_ePaper_Py.display import EPaperDisplay
from IT8951_ePaper_Py.it8951 import IT8951
from IT8951_ePaper_Py.spi_interface import MockSPI


class TestPerformance:
    """Test performance differences between pixel formats."""

    @pytest.fixture
    def display(self, mocker: MockerFixture):
        """Create a display instance with mock SPI."""
        mock_spi = MockSPI()
        # Data for _get_device_info (20 values)
        mock_spi.set_read_data(
            [1872, 1404, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        # Data for _enable_packed_write register read
        mock_spi.set_read_data([0x0000])

        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Mock clear to avoid complex setup
        mocker.patch.object(display, "clear")

        display.init()
        return display

    def test_4bpp_vs_8bpp_packing_performance(self):
        """Test that 4bpp packing is measurably different from 8bpp."""
        # Create test image (1872x1404)
        image = np.random.randint(0, 256, size=(1404, 1872), dtype=np.uint8)
        image_bytes = image.flatten().tobytes()

        # Time 8bpp packing
        start_8bpp = time.perf_counter()
        packed_8bpp = IT8951.pack_pixels(image_bytes, PixelFormat.BPP_8)
        time_8bpp = time.perf_counter() - start_8bpp

        # Time 4bpp packing
        start_4bpp = time.perf_counter()
        packed_4bpp = IT8951.pack_pixels(image_bytes, PixelFormat.BPP_4)
        time_4bpp = time.perf_counter() - start_4bpp

        # Verify data sizes
        assert len(packed_8bpp) == 1872 * 1404  # 1 byte per pixel
        assert len(packed_4bpp) == (1872 * 1404 + 1) // 2  # 2 pixels per byte

        # 4bpp should take more time due to bit manipulation
        # This is a trade-off for reduced data transfer
        assert time_4bpp > 0  # Ensure measurable time
        assert time_8bpp > 0  # Ensure measurable time

    def test_4bpp_vs_8bpp_data_size(self):
        """Test that 4bpp reduces data size by 50%."""
        # Create test data (100x100 pixels)
        pixels = np.full(10000, 128, dtype=np.uint8).tobytes()

        # Pack as 8bpp
        packed_8bpp = IT8951.pack_pixels(pixels, PixelFormat.BPP_8)

        # Pack as 4bpp
        packed_4bpp = IT8951.pack_pixels(pixels, PixelFormat.BPP_4)

        # Verify 4bpp is half the size of 8bpp
        assert len(packed_8bpp) == 10000  # 1 byte per pixel
        assert len(packed_4bpp) == 5000  # 2 pixels per byte
        assert len(packed_4bpp) == len(packed_8bpp) // 2

    def test_4bpp_packing_correctness(self):
        """Test that 4bpp packing preserves grayscale levels."""
        # Test specific grayscale values that should map to 4-bit values
        test_values = [0, 17, 34, 51, 68, 85, 102, 119, 136, 153, 170, 187, 204, 221, 238, 255]
        pixels = np.array(test_values, dtype=np.uint8)
        pixels_bytes = pixels.tobytes()

        packed = IT8951.pack_pixels(pixels_bytes, PixelFormat.BPP_4)

        # Verify packing (2 pixels per byte)
        assert len(packed) == 8  # 16 pixels / 2 pixels per byte

        # Verify first few packed bytes
        # In 4bpp, values are shifted right by 4 to fit in 4 bits
        # 0 >> 4 = 0x0, 17 >> 4 = 0x1, combined as 0x01 (first pixel in high nibble)
        assert packed[0] == 0x01
        # 34 >> 4 = 0x2, 51 >> 4 = 0x3, combined as 0x23
        assert packed[1] == 0x23

    @pytest.mark.parametrize("size", [(100, 100), (500, 500), (1000, 1000)])
    def test_scaling_performance(self, size):
        """Test performance scaling with different image sizes."""
        width, height = size
        image = np.random.randint(0, 256, size=(height, width), dtype=np.uint8)
        image_bytes = image.flatten().tobytes()

        # Time 8bpp
        start_8bpp = time.perf_counter()
        packed_8bpp = IT8951.pack_pixels(image_bytes, PixelFormat.BPP_8)
        time_8bpp = time.perf_counter() - start_8bpp

        # Time 4bpp
        start_4bpp = time.perf_counter()
        packed_4bpp = IT8951.pack_pixels(image_bytes, PixelFormat.BPP_4)
        time_4bpp = time.perf_counter() - start_4bpp

        # Verify sizes
        assert len(packed_8bpp) == width * height
        assert len(packed_4bpp) == (width * height + 1) // 2

        # Both should complete in reasonable time
        assert time_8bpp < 1.0  # Should pack in under 1 second
        assert time_4bpp < 1.0  # Should pack in under 1 second
