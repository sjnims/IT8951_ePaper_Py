"""Optimized pixel packing utilities for IT8951 e-paper driver.

This module provides numpy-optimized implementations of pixel packing functions
for improved performance when working with large images.
"""

from typing import TYPE_CHECKING

import numpy as np

from IT8951_ePaper_Py.constants import PixelFormat, ProtocolConstants
from IT8951_ePaper_Py.exceptions import InvalidParameterError

# Cached arrays for 1bpp packing to avoid repeated allocations
_POWERS_OF_2_CACHE = np.array([128, 64, 32, 16, 8, 4, 2, 1], dtype=np.uint8)

if TYPE_CHECKING:
    from numpy.typing import NDArray

    NumpyArray = NDArray[np.uint8]
else:
    NumpyArray = np.ndarray


def pack_pixels_numpy(pixels: bytes | NumpyArray, pixel_format: PixelFormat) -> bytes:
    """Pack pixel data using numpy optimizations.

    This function provides significantly faster pixel packing for large images
    by using numpy's vectorized operations instead of Python loops.

    Args:
        pixels: 8-bit pixel data (each byte is one pixel).
        pixel_format: Target pixel format.

    Returns:
        Packed pixel data according to format.

    Raises:
        InvalidParameterError: If pixel format is not supported.
    """
    # Convert to numpy array if needed
    if isinstance(pixels, bytes):
        arr = np.frombuffer(pixels, dtype=np.uint8)
    else:
        arr = pixels.astype(np.uint8) if pixels.dtype != np.uint8 else pixels

    # Use dictionary dispatch
    packers = {
        PixelFormat.BPP_8: _pack_8bpp_numpy,
        PixelFormat.BPP_4: _pack_4bpp_numpy,
        PixelFormat.BPP_2: _pack_2bpp_numpy,
        PixelFormat.BPP_1: _pack_1bpp_numpy,
    }

    packer = packers.get(pixel_format)
    if not packer:
        raise InvalidParameterError(f"Pixel format {pixel_format} not yet implemented")

    return packer(arr)


def _pack_8bpp_numpy(arr: NumpyArray) -> bytes:
    """No packing needed for 8bpp."""
    return arr.tobytes()


def _pack_4bpp_numpy(arr: NumpyArray) -> bytes:
    """Pack 2 pixels per byte (4 bits each) using numpy.

    This is ~10-20x faster than the loop-based implementation for large images.
    """
    # Reduce to 4-bit values (0-15 range)
    arr_4bit = arr >> ProtocolConstants.PIXEL_SHIFT_4BPP

    # Pad array to even length if needed
    if len(arr_4bit) % 2 != 0:
        arr_4bit = np.pad(arr_4bit, (0, 1), mode="constant", constant_values=0)

    # Reshape to pairs of pixels
    pairs = arr_4bit.reshape(-1, 2)

    # Pack pairs into bytes (first pixel in high nibble, second in low nibble)
    packed = (pairs[:, 0] << ProtocolConstants.PIXEL_SHIFT_4BPP) | pairs[:, 1]

    return packed.astype(np.uint8).tobytes()


def _pack_2bpp_numpy(arr: NumpyArray) -> bytes:
    """Pack 4 pixels per byte (2 bits each) using numpy.

    This is ~20-30x faster than the loop-based implementation for large images.
    """
    # Reduce to 2-bit values (0-3 range)
    arr_2bit = arr >> 6

    # Pad array to multiple of 4 if needed
    pad_size = (4 - len(arr_2bit) % 4) % 4
    if pad_size > 0:
        arr_2bit = np.pad(arr_2bit, (0, pad_size), mode="constant", constant_values=0)

    # Reshape to groups of 4 pixels
    quads = arr_2bit.reshape(-1, 4)

    # Pack 4 pixels into bytes with proper bit positions
    packed = (quads[:, 0] << 6) | (quads[:, 1] << 4) | (quads[:, 2] << 2) | quads[:, 3]

    return packed.astype(np.uint8).tobytes()


def _pack_1bpp_numpy(arr: NumpyArray) -> bytes:
    """Pack 8 pixels per byte (1 bit each) using numpy.

    This is ~30-50x faster than the loop-based implementation for large images.
    """
    # Convert to binary (0 or 1) using threshold
    binary = (arr >= ProtocolConstants.PIXEL_SHIFT_1BPP_THRESHOLD).astype(np.uint8)

    # Pad array to multiple of 8 if needed
    pad_size = (8 - len(binary) % 8) % 8
    if pad_size > 0:
        binary = np.pad(binary, (0, pad_size), mode="constant", constant_values=0)

    # Reshape to groups of 8 pixels
    octets = binary.reshape(-1, 8)

    # Pack 8 pixels into bytes (MSB first)
    # Use cached powers array to avoid allocation
    packed = np.sum(octets * _POWERS_OF_2_CACHE, axis=1, dtype=np.uint8)

    return packed.tobytes()
