"""Command utilities for IT8951 e-paper driver.

This module provides shared utilities for command operations and validation.
"""

from dataclasses import dataclass

from IT8951_ePaper_Py.constants import ProtocolConstants
from IT8951_ePaper_Py.exceptions import InvalidParameterError, IT8951MemoryError


@dataclass
class Rectangle:
    """Rectangle with position and size."""

    x: int
    y: int
    width: int
    height: int


@dataclass
class Bounds:
    """Panel bounds."""

    width: int
    height: int


def validate_memory_address(address: int) -> None:
    """Validate that a memory address is within valid range.

    Args:
        address: Memory address to validate.

    Raises:
        IT8951MemoryError: If address is invalid.
    """
    if address < 0 or address > ProtocolConstants.MAX_ADDRESS:
        raise IT8951MemoryError(f"Invalid memory address: 0x{address:08X}")


def split_address_16bit(address: int) -> tuple[int, int]:
    """Split a 32-bit address into two 16-bit parts.

    Args:
        address: 32-bit address to split.

    Returns:
        Tuple of (low_16_bits, high_16_bits).
    """
    low = address & ProtocolConstants.ADDRESS_MASK
    high = (address >> ProtocolConstants.ADDRESS_SHIFT_16) & ProtocolConstants.ADDRESS_MASK
    return low, high


def combine_address_16bit(low: int, high: int) -> int:
    """Combine two 16-bit parts into a 32-bit address.

    Args:
        low: Low 16 bits.
        high: High 16 bits.

    Returns:
        Combined 32-bit address.
    """
    return (high << ProtocolConstants.ADDRESS_SHIFT_16) | low


def validate_voltage_range(voltage: float, min_voltage: float, max_voltage: float) -> None:
    """Validate that a voltage is within the specified range.

    Args:
        voltage: Voltage to validate.
        min_voltage: Minimum allowed voltage.
        max_voltage: Maximum allowed voltage.

    Raises:
        InvalidParameterError: If voltage is out of range.
    """
    if voltage < min_voltage or voltage > max_voltage:
        raise InvalidParameterError(
            f"Voltage {voltage}V out of range. Must be between {min_voltage}V and {max_voltage}V"
        )


def pack_bytes_to_words(data: bytes) -> list[int]:
    """Pack bytes into 16-bit words for SPI transmission.

    Args:
        data: Byte data to pack.

    Returns:
        List of 16-bit words.
    """
    words: list[int] = []
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            word = (data[i] << ProtocolConstants.BYTE_SHIFT) | data[i + 1]
        else:
            # Pad with zero if odd number of bytes
            word = data[i] << ProtocolConstants.BYTE_SHIFT
        words.append(word)
    return words


def validate_dimensions(width: int, height: int, max_width: int, max_height: int) -> None:
    """Validate dimensions are within bounds.

    Args:
        width: Width to validate.
        height: Height to validate.
        max_width: Maximum allowed width.
        max_height: Maximum allowed height.

    Raises:
        InvalidParameterError: If dimensions exceed bounds.
    """
    if width <= 0 or height <= 0:
        raise InvalidParameterError(f"Invalid dimensions: {width}x{height} (must be positive)")

    if width > max_width or height > max_height:
        raise InvalidParameterError(
            f"Dimensions {width}x{height} exceed maximum {max_width}x{max_height}"
        )


def validate_rectangle(rect: Rectangle, bounds: Bounds) -> None:
    """Validate that a rectangle fits within panel bounds.

    Args:
        rect: Rectangle to validate.
        bounds: Panel bounds.

    Raises:
        InvalidParameterError: If rectangle exceeds panel bounds.
    """
    if rect.x < 0 or rect.y < 0:
        raise InvalidParameterError(
            f"Invalid coordinates: ({rect.x}, {rect.y}) (must be non-negative)"
        )

    if rect.x + rect.width > bounds.width:
        raise InvalidParameterError(
            f"Rectangle at ({rect.x}, {rect.y}) with width {rect.width} "
            f"exceeds panel width {bounds.width}"
        )

    if rect.y + rect.height > bounds.height:
        raise InvalidParameterError(
            f"Rectangle at ({rect.x}, {rect.y}) with height {rect.height} "
            f"exceeds panel height {bounds.height}"
        )
