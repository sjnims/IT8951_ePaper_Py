"""Tests for pixel packing functionality."""

import numpy as np
import pytest

from IT8951_ePaper_Py.constants import PixelFormat
from IT8951_ePaper_Py.exceptions import InvalidParameterError
from IT8951_ePaper_Py.it8951 import IT8951
from IT8951_ePaper_Py.pixel_packing import pack_pixels_numpy


class TestPixelPacking:
    """Test pixel packing for different bit depths."""

    def test_pack_pixels_8bpp(self) -> None:
        """Test 8bpp packing (no change)."""
        pixels = bytes([0, 64, 128, 192, 255])
        packed = IT8951.pack_pixels(pixels, PixelFormat.BPP_8)
        assert packed == pixels

    def test_pack_pixels_4bpp(self) -> None:
        """Test 4bpp packing (2 pixels per byte)."""
        # Input: 8-bit pixels (0-255)
        pixels = bytes([0x00, 0xFF, 0x80, 0x40, 0xC0, 0x20])

        # Expected: each pixel >> 4, packed 2 per byte
        # 0x00 >> 4 = 0x0, 0xFF >> 4 = 0xF -> 0x0F
        # 0x80 >> 4 = 0x8, 0x40 >> 4 = 0x4 -> 0x84
        # 0xC0 >> 4 = 0xC, 0x20 >> 4 = 0x2 -> 0xC2
        expected = bytes([0x0F, 0x84, 0xC2])

        packed = IT8951.pack_pixels(pixels, PixelFormat.BPP_4)
        assert packed == expected

    def test_pack_pixels_4bpp_odd_length(self) -> None:
        """Test 4bpp packing with odd number of pixels."""
        pixels = bytes([0xF0, 0x80, 0x40])

        # 0xF0 >> 4 = 0xF, 0x80 >> 4 = 0x8 -> 0xF8
        # 0x40 >> 4 = 0x4, 0x00 (padding) -> 0x40
        expected = bytes([0xF8, 0x40])

        packed = IT8951.pack_pixels(pixels, PixelFormat.BPP_4)
        assert packed == expected

    def test_pack_pixels_2bpp(self) -> None:
        """Test 2bpp packing (4 pixels per byte)."""
        # Input: 8-bit pixels (0-255)
        pixels = bytes([0x00, 0xFF, 0x80, 0x40, 0xC0, 0x20, 0x60, 0xA0])

        # Expected: each pixel >> 6, packed 4 per byte
        # 0x00 >> 6 = 0, 0xFF >> 6 = 3, 0x80 >> 6 = 2, 0x40 >> 6 = 1 -> 0b00111001 = 0x39
        # 0xC0 >> 6 = 3, 0x20 >> 6 = 0, 0x60 >> 6 = 1, 0xA0 >> 6 = 2 -> 0b11000110 = 0xC6
        expected = bytes([0x39, 0xC6])

        packed = IT8951.pack_pixels(pixels, PixelFormat.BPP_2)
        assert packed == expected

    def test_pack_pixels_2bpp_partial(self) -> None:
        """Test 2bpp packing with less than 4 pixels."""
        pixels = bytes([0xC0, 0x80])

        # 0xC0 >> 6 = 3, 0x80 >> 6 = 2, padding 0, 0 -> 0b11100000 = 0xE0
        expected = bytes([0xE0])

        packed = IT8951.pack_pixels(pixels, PixelFormat.BPP_2)
        assert packed == expected

    def test_pack_pixels_1bpp(self) -> None:
        """Test 1bpp pixel packing (8 pixels per byte)."""
        # Test threshold: pixels < 128 -> 0, pixels >= 128 -> 1
        pixels = bytes([0, 255, 100, 200, 50, 150, 0, 255])  # 0,1,0,1,0,1,0,1
        expected = bytes([0b01010101])  # MSB first
        packed = IT8951.pack_pixels(pixels, PixelFormat.BPP_1)
        assert packed == expected

        # Test partial byte
        pixels = bytes([0, 255, 128])  # 0,1,1 -> 0b01100000
        expected = bytes([0b01100000])
        packed = IT8951.pack_pixels(pixels, PixelFormat.BPP_1)
        assert packed == expected

        # Test all black (0)
        pixels = bytes([0, 50, 100, 127, 0, 0, 0, 0])  # All < 128 -> 0
        expected = bytes([0b00000000])
        packed = IT8951.pack_pixels(pixels, PixelFormat.BPP_1)
        assert packed == expected

        # Test all white (1)
        pixels = bytes([128, 255, 200, 150, 255, 255, 255, 255])  # All >= 128 -> 1
        expected = bytes([0b11111111])
        packed = IT8951.pack_pixels(pixels, PixelFormat.BPP_1)
        assert packed == expected

    def test_pack_pixels_invalid_format(self) -> None:
        """Test invalid pixel format raises error."""
        pixels = bytes([0, 255])

        # Test with an invalid format value
        with pytest.raises(InvalidParameterError, match="not yet implemented"):
            IT8951.pack_pixels(pixels, 99)  # type: ignore[arg-type]

    def test_pack_pixels_empty(self) -> None:
        """Test packing empty pixel data."""
        pixels = b""

        # Should return empty bytes for any format
        assert IT8951.pack_pixels(pixels, PixelFormat.BPP_8) == b""
        assert IT8951.pack_pixels(pixels, PixelFormat.BPP_4) == b""
        assert IT8951.pack_pixels(pixels, PixelFormat.BPP_2) == b""
        assert IT8951.pack_pixels(pixels, PixelFormat.BPP_1) == b""

    def test_pack_pixels_preserves_grayscale_levels(self) -> None:
        """Test that packing preserves appropriate grayscale levels."""
        # Create pixels with values that map to each 4-bit level
        pixels_4bit = bytes([i * 16 for i in range(16)])  # 0, 16, 32, ..., 240

        packed = IT8951.pack_pixels(pixels_4bit, PixelFormat.BPP_4)

        # Verify we get 8 bytes (16 pixels / 2)
        assert len(packed) == 8

        # Unpack and verify levels
        unpacked = []
        for byte in packed:
            unpacked.append((byte >> 4) << 4)  # High nibble -> full byte
            unpacked.append((byte & 0x0F) << 4)  # Low nibble -> full byte

        # Each original pixel should round down to nearest 16
        for i, (original, restored) in enumerate(zip(pixels_4bit, unpacked, strict=True)):
            expected = (original // 16) * 16
            assert restored == expected, f"Pixel {i}: {original} -> {restored}, expected {expected}"

    def test_convert_endian_1bpp_no_change(self) -> None:
        """Test endian conversion with no bit reversal."""
        data = bytes([0b10110010, 0b01001101, 0b11110000])
        result = IT8951.convert_endian_1bpp(data, reverse_bits=False)
        assert result == data

    def test_convert_endian_1bpp_reverse_bits(self) -> None:
        """Test endian conversion with bit reversal."""
        # Test single byte
        data = bytes([0b10110010])  # MSB first
        expected = bytes([0b01001101])  # LSB first
        result = IT8951.convert_endian_1bpp(data, reverse_bits=True)
        assert result == expected

        # Test multiple bytes
        data = bytes([0b11110000, 0b10101010, 0b00001111])
        expected = bytes([0b00001111, 0b01010101, 0b11110000])
        result = IT8951.convert_endian_1bpp(data, reverse_bits=True)
        assert result == expected

        # Test edge cases
        assert IT8951.convert_endian_1bpp(bytes([0xFF]), reverse_bits=True) == bytes([0xFF])
        assert IT8951.convert_endian_1bpp(bytes([0x00]), reverse_bits=True) == bytes([0x00])
        assert IT8951.convert_endian_1bpp(bytes([0x80]), reverse_bits=True) == bytes([0x01])
        assert IT8951.convert_endian_1bpp(bytes([0x01]), reverse_bits=True) == bytes([0x80])

    def test_convert_endian_1bpp_empty(self) -> None:
        """Test endian conversion with empty data."""
        assert IT8951.convert_endian_1bpp(b"", reverse_bits=False) == b""
        assert IT8951.convert_endian_1bpp(b"", reverse_bits=True) == b""


class TestPixelPackingNumpy:
    """Test numpy-optimized pixel packing functions directly."""

    def test_pack_pixels_numpy_8bpp_bytes(self) -> None:
        """Test 8bpp packing with bytes input (no change)."""
        pixels = bytes([0, 64, 128, 192, 255])
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_8)
        assert packed == pixels

    def test_pack_pixels_numpy_8bpp_array(self) -> None:
        """Test 8bpp packing with numpy array input."""
        pixels = np.array([0, 64, 128, 192, 255], dtype=np.uint8)
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_8)
        assert packed == bytes([0, 64, 128, 192, 255])

    def test_pack_pixels_numpy_8bpp_different_dtype(self) -> None:
        """Test 8bpp packing with non-uint8 array."""
        pixels = np.array([0, 64, 128, 192, 255], dtype=np.int32)
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_8)
        assert packed == bytes([0, 64, 128, 192, 255])

    def test_pack_pixels_numpy_4bpp_bytes(self) -> None:
        """Test 4bpp packing with bytes input."""
        pixels = bytes([0x00, 0xFF, 0x80, 0x40, 0xC0, 0x20])
        expected = bytes([0x0F, 0x84, 0xC2])
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_4)
        assert packed == expected

    def test_pack_pixels_numpy_4bpp_array(self) -> None:
        """Test 4bpp packing with numpy array."""
        pixels = np.array([0x00, 0xFF, 0x80, 0x40, 0xC0, 0x20], dtype=np.uint8)
        expected = bytes([0x0F, 0x84, 0xC2])
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_4)
        assert packed == expected

    def test_pack_pixels_numpy_4bpp_odd_length(self) -> None:
        """Test 4bpp packing with odd number of pixels."""
        pixels = np.array([0xF0, 0x80, 0x40], dtype=np.uint8)
        expected = bytes([0xF8, 0x40])
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_4)
        assert packed == expected

    def test_pack_pixels_numpy_4bpp_empty(self) -> None:
        """Test 4bpp packing with empty data."""
        pixels = np.array([], dtype=np.uint8)
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_4)
        assert packed == b""

    def test_pack_pixels_numpy_2bpp_bytes(self) -> None:
        """Test 2bpp packing with bytes input."""
        pixels = bytes([0x00, 0xFF, 0x80, 0x40, 0xC0, 0x20, 0x60, 0xA0])
        expected = bytes([0x39, 0xC6])
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_2)
        assert packed == expected

    def test_pack_pixels_numpy_2bpp_array(self) -> None:
        """Test 2bpp packing with numpy array."""
        pixels = np.array([0x00, 0xFF, 0x80, 0x40, 0xC0, 0x20, 0x60, 0xA0], dtype=np.uint8)
        expected = bytes([0x39, 0xC6])
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_2)
        assert packed == expected

    def test_pack_pixels_numpy_2bpp_partial(self) -> None:
        """Test 2bpp packing with less than 4 pixels."""
        # Test with 1 pixel
        pixels = np.array([0xC0], dtype=np.uint8)
        expected = bytes([0xC0])  # 11000000
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_2)
        assert packed == expected

        # Test with 2 pixels
        pixels = np.array([0xC0, 0x80], dtype=np.uint8)
        expected = bytes([0xE0])  # 11100000
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_2)
        assert packed == expected

        # Test with 3 pixels
        pixels = np.array([0xC0, 0x80, 0x40], dtype=np.uint8)
        expected = bytes([0xE4])  # 11100100
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_2)
        assert packed == expected

    def test_pack_pixels_numpy_2bpp_empty(self) -> None:
        """Test 2bpp packing with empty data."""
        pixels = np.array([], dtype=np.uint8)
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_2)
        assert packed == b""

    def test_pack_pixels_numpy_1bpp_bytes(self) -> None:
        """Test 1bpp packing with bytes input."""
        pixels = bytes([0, 255, 100, 200, 50, 150, 0, 255])
        expected = bytes([0b01010101])  # MSB first
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_1)
        assert packed == expected

    def test_pack_pixels_numpy_1bpp_array(self) -> None:
        """Test 1bpp packing with numpy array."""
        pixels = np.array([0, 255, 100, 200, 50, 150, 0, 255], dtype=np.uint8)
        expected = bytes([0b01010101])
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_1)
        assert packed == expected

    def test_pack_pixels_numpy_1bpp_partial(self) -> None:
        """Test 1bpp packing with partial byte."""
        # Test with 1 pixel
        pixels = np.array([255], dtype=np.uint8)
        expected = bytes([0b10000000])
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_1)
        assert packed == expected

        # Test with 3 pixels
        pixels = np.array([0, 255, 128], dtype=np.uint8)
        expected = bytes([0b01100000])
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_1)
        assert packed == expected

        # Test with 7 pixels
        pixels = np.array([255, 0, 255, 0, 255, 0, 255], dtype=np.uint8)
        expected = bytes([0b10101010])
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_1)
        assert packed == expected

    def test_pack_pixels_numpy_1bpp_threshold(self) -> None:
        """Test 1bpp threshold behavior (128)."""
        # Values below 128 -> 0
        pixels = np.array([0, 50, 100, 127], dtype=np.uint8)
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_1)
        assert packed == bytes([0b00000000])

        # Values >= 128 -> 1
        pixels = np.array([128, 150, 200, 255], dtype=np.uint8)
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_1)
        assert packed == bytes([0b11110000])

    def test_pack_pixels_numpy_1bpp_empty(self) -> None:
        """Test 1bpp packing with empty data."""
        pixels = np.array([], dtype=np.uint8)
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_1)
        assert packed == b""

    def test_pack_pixels_numpy_invalid_format(self) -> None:
        """Test invalid pixel format raises error."""
        pixels = bytes([0, 255])

        # Test with an invalid format value
        with pytest.raises(InvalidParameterError, match="Pixel format .* not yet implemented"):
            pack_pixels_numpy(pixels, 99)  # type: ignore[arg-type]

    def test_pack_pixels_numpy_empty_bytes(self) -> None:
        """Test packing empty bytes for all formats."""
        pixels = b""

        assert pack_pixels_numpy(pixels, PixelFormat.BPP_8) == b""
        assert pack_pixels_numpy(pixels, PixelFormat.BPP_4) == b""
        assert pack_pixels_numpy(pixels, PixelFormat.BPP_2) == b""
        assert pack_pixels_numpy(pixels, PixelFormat.BPP_1) == b""

    def test_pack_pixels_numpy_large_data(self) -> None:
        """Test packing with larger data to verify performance optimizations."""
        # Create a 1024x768 image worth of pixels
        size = 1024 * 768
        pixels = np.random.randint(0, 256, size=size, dtype=np.uint8)

        # Test all formats work with large data
        packed_8bpp = pack_pixels_numpy(pixels, PixelFormat.BPP_8)
        assert len(packed_8bpp) == size

        packed_4bpp = pack_pixels_numpy(pixels, PixelFormat.BPP_4)
        assert len(packed_4bpp) == size // 2

        packed_2bpp = pack_pixels_numpy(pixels, PixelFormat.BPP_2)
        assert len(packed_2bpp) == size // 4

        packed_1bpp = pack_pixels_numpy(pixels, PixelFormat.BPP_1)
        assert len(packed_1bpp) == size // 8

    def test_pack_pixels_numpy_powers_of_2_cache(self) -> None:
        """Test that 1bpp packing uses the cached powers array correctly."""
        # This indirectly tests the _POWERS_OF_2_CACHE usage
        pixels = np.array([255, 255, 255, 255, 255, 255, 255, 255], dtype=np.uint8)
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_1)
        assert packed == bytes([0xFF])

        pixels = np.array([255, 0, 255, 0, 255, 0, 255, 0], dtype=np.uint8)
        packed = pack_pixels_numpy(pixels, PixelFormat.BPP_1)
        assert packed == bytes([0xAA])
