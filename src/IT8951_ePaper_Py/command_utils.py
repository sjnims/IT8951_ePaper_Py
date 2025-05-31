"""Command utilities for IT8951 e-paper driver.

This module provides shared utilities for command operations and validation
used throughout the IT8951 driver. These utilities handle common tasks like:

- Memory address validation and manipulation
- Voltage range validation
- Dimension and coordinate validation
- Data packing for SPI transmission
- Rectangle bounds checking

These functions ensure data integrity and prevent hardware errors by
validating inputs before they reach the IT8951 controller.
"""

from dataclasses import dataclass

from IT8951_ePaper_Py.constants import ProtocolConstants
from IT8951_ePaper_Py.exceptions import InvalidParameterError, IT8951MemoryError


@dataclass
class Rectangle:
    """Rectangle with position and size.

    Represents a rectangular area on the display, used for partial
    updates and area validation.

    Attributes:
        x: Left edge X coordinate in pixels.
        y: Top edge Y coordinate in pixels.
        width: Rectangle width in pixels.
        height: Rectangle height in pixels.
    """

    x: int
    y: int
    width: int
    height: int


@dataclass
class Bounds:
    """Panel bounds.

    Represents the total display panel dimensions, used for validating
    that operations stay within the physical display boundaries.

    Attributes:
        width: Panel width in pixels.
        height: Panel height in pixels.
    """

    width: int
    height: int


def validate_memory_address(address: int) -> None:
    """Validate that a memory address is within valid range.

    The IT8951 controller has a specific memory address space that can be
    accessed. This function ensures addresses are within the valid range
    to prevent hardware errors or undefined behavior.

    Args:
        address: Memory address to validate. Must be a 32-bit value
            between 0 and MAX_ADDRESS (0xFFFFFFFF).

    Raises:
        IT8951MemoryError: If address is negative or exceeds the maximum
            addressable memory space.

    Examples:
        >>> validate_memory_address(0x1000)  # Valid
        >>> validate_memory_address(-1)  # Raises IT8951MemoryError
        >>> validate_memory_address(0x100000000)  # Raises IT8951MemoryError

    Note:
        This validation is critical when working with direct memory
        operations like load_image_area().
    """
    if address < 0 or address > ProtocolConstants.MAX_ADDRESS:
        raise IT8951MemoryError(f"Invalid memory address: 0x{address:08X}")


def split_address_16bit(address: int) -> tuple[int, int]:
    """Split a 32-bit address into two 16-bit parts.

    The IT8951 requires 32-bit addresses to be sent as two 16-bit values
    over the SPI interface. This function performs the split correctly,
    preserving the address when recombined.

    Args:
        address: 32-bit memory address to split.

    Returns:
        Tuple containing:
        - low: Lower 16 bits (bits 0-15)
        - high: Upper 16 bits (bits 16-31)

    Examples:
        >>> split_address_16bit(0x12345678)
        (0x5678, 0x1234)
        >>> split_address_16bit(0x1000)
        (0x1000, 0x0000)
        >>> low, high = split_address_16bit(0xABCD1234)
        >>> hex(low), hex(high)
        ('0x1234', '0xabcd')

    Note:
        Used internally by commands that need to send memory addresses
        to the IT8951 controller.
    """
    low = address & ProtocolConstants.ADDRESS_MASK
    high = (address >> ProtocolConstants.ADDRESS_SHIFT_16) & ProtocolConstants.ADDRESS_MASK
    return low, high


def combine_address_16bit(low: int, high: int) -> int:
    """Combine two 16-bit parts into a 32-bit address.

    Reverses the operation of split_address_16bit(), reconstructing
    a 32-bit address from its two 16-bit components.

    Args:
        low: Lower 16 bits (bits 0-15) of the address.
        high: Upper 16 bits (bits 16-31) of the address.

    Returns:
        Combined 32-bit memory address.

    Examples:
        >>> combine_address_16bit(0x5678, 0x1234)
        0x12345678
        >>> combine_address_16bit(0x1000, 0x0000)
        0x1000
        >>> addr = 0xABCD1234
        >>> low, high = split_address_16bit(addr)
        >>> combine_address_16bit(low, high) == addr
        True

    Note:
        This is the inverse of split_address_16bit() and is used when
        reading addresses back from the IT8951.
    """
    return (high << ProtocolConstants.ADDRESS_SHIFT_16) | low


def validate_voltage_range(voltage: float, min_voltage: float, max_voltage: float) -> None:
    """Validate that a voltage is within the specified range.

    Used primarily for VCOM voltage validation to ensure the voltage
    supplied to the e-paper display is safe and within specifications.
    Incorrect voltages can damage the display or cause poor image quality.

    Args:
        voltage: Voltage value to validate (in volts).
        min_voltage: Minimum allowed voltage (typically negative for VCOM).
        max_voltage: Maximum allowed voltage (typically less negative).

    Raises:
        InvalidParameterError: If voltage is outside the allowed range.
            The error message includes the valid range for reference.

    Examples:
        >>> validate_voltage_range(-2.0, -3.0, -0.2)  # Valid VCOM
        >>> validate_voltage_range(-3.5, -3.0, -0.2)  # Raises error
        >>> validate_voltage_range(0.0, -3.0, -0.2)   # Raises error

    Note:
        VCOM voltages are typically negative values between -3.0V and -0.2V.
        The exact range depends on your specific e-paper panel.
    """
    if voltage < min_voltage or voltage > max_voltage:
        raise InvalidParameterError(
            f"Voltage {voltage}V out of range. Must be between {min_voltage}V and {max_voltage}V"
        )


def pack_bytes_to_words(data: bytes) -> list[int]:
    r"""Pack bytes into 16-bit words for SPI transmission.

    The IT8951's SPI interface expects data in 16-bit word format.
    This function converts byte arrays into the required format,
    handling odd-length data by padding with zeros.

    Args:
        data: Raw byte data to pack. Can be any length.

    Returns:
        List of 16-bit words where each word contains two bytes
        from the input data (MSB first).

    Examples:
        >>> pack_bytes_to_words(b'\x12\x34\x56\x78')
        [0x1234, 0x5678]
        >>> pack_bytes_to_words(b'\x12\x34\x56')  # Odd length
        [0x1234, 0x5600]  # Padded with 0x00
        >>> pack_bytes_to_words(b'')  # Empty
        []

    Note:
        - Bytes are packed MSB-first (big-endian) into words
        - Odd-length data is padded with a zero byte
        - Used internally for bulk data transfers
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

    Ensures that image or display area dimensions are positive and don't
    exceed the physical limitations of the display panel. This prevents
    memory access errors and display corruption.

    Args:
        width: Width to validate in pixels. Must be positive.
        height: Height to validate in pixels. Must be positive.
        max_width: Maximum allowed width (typically panel width).
        max_height: Maximum allowed height (typically panel height).

    Raises:
        InvalidParameterError: If dimensions are non-positive or exceed
            the maximum allowed values.

    Examples:
        >>> validate_dimensions(800, 600, 1872, 1404)  # Valid
        >>> validate_dimensions(0, 600, 1872, 1404)    # Raises error
        >>> validate_dimensions(2000, 600, 1872, 1404) # Raises error

    Note:
        Common display sizes:
        - 10.3" panel: 1872x1404
        - 7.8" panel: 1872x1404
        - 6" panel: 1448x1072
    """
    if width <= 0 or height <= 0:
        raise InvalidParameterError(f"Invalid dimensions: {width}x{height} (must be positive)")

    if width > max_width or height > max_height:
        raise InvalidParameterError(
            f"Dimensions {width}x{height} exceed maximum {max_width}x{max_height}"
        )


def validate_rectangle(rect: Rectangle, bounds: Bounds) -> None:
    """Validate that a rectangle fits within panel bounds.

    Comprehensive validation to ensure a display area rectangle is
    completely contained within the physical display panel. This prevents
    attempts to update areas outside the visible display.

    Args:
        rect: Rectangle defining the area to validate. All coordinates
            and dimensions must be non-negative.
        bounds: Physical panel boundaries to validate against.

    Raises:
        InvalidParameterError: If any of these conditions are true:
            - Rectangle has negative coordinates (x < 0 or y < 0)
            - Rectangle extends past right edge (x + width > panel_width)
            - Rectangle extends past bottom edge (y + height > panel_height)

    Examples:
        >>> # 10.3" panel example
        >>> panel = Bounds(width=1872, height=1404)
        >>>
        >>> # Valid: fully contained rectangle
        >>> rect1 = Rectangle(x=100, y=100, width=500, height=400)
        >>> validate_rectangle(rect1, panel)  # OK
        >>>
        >>> # Invalid: extends past right edge
        >>> rect2 = Rectangle(x=1500, y=100, width=500, height=400)
        >>> validate_rectangle(rect2, panel)  # Raises error
        >>>
        >>> # Invalid: negative coordinates
        >>> rect3 = Rectangle(x=-10, y=100, width=500, height=400)
        >>> validate_rectangle(rect3, panel)  # Raises error

    Note:
        This validation is performed before every display update to ensure
        hardware safety and prevent undefined behavior.
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
