"""Tests for numpy-optimized pixel packing."""

import numpy as np

from IT8951_ePaper_Py.constants import PixelFormat
from IT8951_ePaper_Py.it8951 import IT8951
from IT8951_ePaper_Py.pixel_packing import (
    _pack_1bpp_numpy,
    _pack_2bpp_numpy,
    _pack_4bpp_numpy,
    _pack_8bpp_numpy,
    pack_pixels_numpy,
)


class TestNumpyPixelPacking:
    """Test numpy-optimized pixel packing functions."""

    def test_pack_8bpp_numpy(self) -> None:
        """Test 8bpp packing (no-op)."""
        data = np.array([0x00, 0x55, 0xAA, 0xFF], dtype=np.uint8)
        result = _pack_8bpp_numpy(data)
        assert result == bytes([0x00, 0x55, 0xAA, 0xFF])

    def test_pack_4bpp_numpy(self) -> None:
        """Test 4bpp packing with numpy."""
        # Test basic packing
        data = np.array([0x00, 0x11, 0x88, 0xFF], dtype=np.uint8)
        result = _pack_4bpp_numpy(data)
        # 0x00 -> 0, 0x11 -> 1, 0x88 -> 8, 0xFF -> F
        # Packed: 0x01, 0x8F
        assert result == bytes([0x01, 0x8F])

        # Test odd length (should pad with 0)
        data = np.array([0xFF, 0x88, 0x44], dtype=np.uint8)
        result = _pack_4bpp_numpy(data)
        # 0xFF -> F, 0x88 -> 8, 0x44 -> 4, pad -> 0
        # Packed: 0xF8, 0x40
        assert result == bytes([0xF8, 0x40])

    def test_pack_2bpp_numpy(self) -> None:
        """Test 2bpp packing with numpy."""
        # Test basic packing (values reduced to 2 bits by >> 6)
        data = np.array([0x00, 0x55, 0xAA, 0xFF], dtype=np.uint8)
        result = _pack_2bpp_numpy(data)
        # 0x00 >> 6 = 0b00, 0x55 >> 6 = 0b01, 0xAA >> 6 = 0b10, 0xFF >> 6 = 0b11
        # Packed: 0b00011011 = 0x1B
        assert result == bytes([0x1B])

        # Test padding
        data = np.array([0xFF, 0xC0, 0x80, 0x40, 0x00], dtype=np.uint8)
        result = _pack_2bpp_numpy(data)
        # 0xFF >> 6 = 3, 0xC0 >> 6 = 3, 0x80 >> 6 = 2, 0x40 >> 6 = 1
        # 0x00 >> 6 = 0, pad = 0, pad = 0, pad = 0
        # First byte: 0b11111001 = 0xF9
        # Second byte: 0b00000000 = 0x00
        assert result == bytes([0xF9, 0x00])

    def test_pack_1bpp_numpy(self) -> None:
        """Test 1bpp packing with numpy."""
        # Test threshold-based packing (threshold = 128)
        # Values < 128 become 0, values >= 128 become 1
        data = np.array([0, 127, 128, 255, 0, 255, 128, 127], dtype=np.uint8)
        result = _pack_1bpp_numpy(data)
        # Binary: 0, 0, 1, 1, 0, 1, 1, 0
        # Packed (MSB first): 0b00110110 = 0x36
        assert result == bytes([0x36])

        # Test padding
        data = np.array([255, 0, 255], dtype=np.uint8)
        result = _pack_1bpp_numpy(data)
        # Binary: 1, 0, 1, 0, 0, 0, 0, 0 (padded)
        # Packed: 0b10100000 = 0xA0
        assert result == bytes([0xA0])

    def test_pack_pixels_numpy_dispatch(self) -> None:
        """Test the main dispatch function."""
        data = np.array([0x00, 0x55, 0xAA, 0xFF], dtype=np.uint8)

        # Test each format
        for pixel_format in [
            PixelFormat.BPP_8,
            PixelFormat.BPP_4,
            PixelFormat.BPP_2,
            PixelFormat.BPP_1,
        ]:
            result_numpy = pack_pixels_numpy(data, pixel_format)
            result_original = IT8951.pack_pixels(data.tobytes(), pixel_format)
            assert result_numpy == result_original

    def test_pack_pixels_numpy_bytes_input(self) -> None:
        """Test that bytes input works correctly."""
        data_bytes = bytes([0x00, 0x55, 0xAA, 0xFF])
        data_array = np.array([0x00, 0x55, 0xAA, 0xFF], dtype=np.uint8)

        for pixel_format in [PixelFormat.BPP_4, PixelFormat.BPP_2, PixelFormat.BPP_1]:
            result_bytes = pack_pixels_numpy(data_bytes, pixel_format)
            result_array = pack_pixels_numpy(data_array, pixel_format)
            assert result_bytes == result_array

    def test_pack_pixels_numpy_large_data(self) -> None:
        """Test packing with larger data sizes."""
        # Create 1KB of test data
        data = np.random.randint(0, 256, 1024, dtype=np.uint8)

        for pixel_format in [PixelFormat.BPP_4, PixelFormat.BPP_2, PixelFormat.BPP_1]:
            result_numpy = pack_pixels_numpy(data, pixel_format)
            result_original = IT8951.pack_pixels(data.tobytes(), pixel_format)
            assert result_numpy == result_original

    def test_it8951_auto_numpy_usage(self) -> None:
        """Test that IT8951.pack_pixels automatically uses numpy for large data."""
        # Create data that triggers numpy usage (> 10000 bytes)
        large_data = bytes(range(256)) * 50  # 12800 bytes
        small_data = bytes(range(256))  # 256 bytes

        # Both should produce the same results
        for pixel_format in [PixelFormat.BPP_4, PixelFormat.BPP_2, PixelFormat.BPP_1]:
            # Large data should use numpy path
            result_large = IT8951.pack_pixels(large_data, pixel_format)
            expected_large = pack_pixels_numpy(large_data, pixel_format)
            assert result_large == expected_large

            # Small data should use original path but still match
            result_small = IT8951.pack_pixels(small_data, pixel_format)
            expected_small = pack_pixels_numpy(small_data, pixel_format)
            assert result_small == expected_small

    def test_pack_pixels_numpy_edge_cases(self) -> None:
        """Test edge cases for numpy packing."""
        # Empty data
        empty = np.array([], dtype=np.uint8)
        assert _pack_8bpp_numpy(empty) == b""
        assert _pack_4bpp_numpy(empty) == b""
        assert _pack_2bpp_numpy(empty) == b""
        assert _pack_1bpp_numpy(empty) == b""

        # Single pixel
        single = np.array([0xFF], dtype=np.uint8)
        assert _pack_8bpp_numpy(single) == bytes([0xFF])
        assert _pack_4bpp_numpy(single) == bytes([0xF0])  # Padded with 0
        assert _pack_2bpp_numpy(single) == bytes([0xC0])  # 0xFF >> 6 = 3, then 0b11000000
        assert _pack_1bpp_numpy(single) == bytes([0x80])  # 1 bit set, 7 padding bits

    def test_pack_pixels_performance_characteristics(self) -> None:
        """Test that numpy version is actually faster for large images."""
        import time

        # Create a realistic image size (800x600)
        data = np.random.randint(0, 256, 800 * 600, dtype=np.uint8)
        data_bytes = data.tobytes()

        # Time original implementation
        start = time.perf_counter()
        _ = IT8951._pack_4bpp(data_bytes)
        time_original = time.perf_counter() - start

        # Time numpy implementation
        start = time.perf_counter()
        _ = _pack_4bpp_numpy(data)
        time_numpy = time.perf_counter() - start

        # Numpy should be significantly faster (at least 5x for this size)
        speedup = time_original / time_numpy
        assert speedup > 5.0, f"Numpy speedup only {speedup:.1f}x, expected > 5x"
