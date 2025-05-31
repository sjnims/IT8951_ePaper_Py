"""Tests for command utilities module."""

import pytest

from IT8951_ePaper_Py.command_utils import (
    Bounds,
    Rectangle,
    combine_address_16bit,
    pack_bytes_to_words,
    split_address_16bit,
    validate_dimensions,
    validate_memory_address,
    validate_rectangle,
    validate_voltage_range,
)
from IT8951_ePaper_Py.exceptions import InvalidParameterError, IT8951MemoryError


class TestCommandUtils:
    """Test command utilities."""

    def test_validate_memory_address_valid(self) -> None:
        """Test validating a valid memory address."""
        # Should not raise
        validate_memory_address(0x001236E0)
        validate_memory_address(0)
        validate_memory_address(0xFFFFFFFF)

    def test_validate_memory_address_invalid(self) -> None:
        """Test validating invalid memory addresses."""
        with pytest.raises(IT8951MemoryError, match="Invalid memory address"):
            validate_memory_address(-1)

        with pytest.raises(IT8951MemoryError, match="Invalid memory address"):
            validate_memory_address(0x100000000)  # Exceeds 32-bit

    def test_split_address_16bit(self) -> None:
        """Test splitting 32-bit address into 16-bit parts."""
        # Test typical image buffer address
        low, high = split_address_16bit(0x001236E0)
        assert low == 0x36E0
        assert high == 0x0012

        # Test edge cases
        low, high = split_address_16bit(0)
        assert low == 0
        assert high == 0

        low, high = split_address_16bit(0xFFFFFFFF)
        assert low == 0xFFFF
        assert high == 0xFFFF

    def test_combine_address_16bit(self) -> None:
        """Test combining 16-bit parts into 32-bit address."""
        # Test typical image buffer address
        address = combine_address_16bit(0x36E0, 0x0012)
        assert address == 0x001236E0

        # Test edge cases
        address = combine_address_16bit(0, 0)
        assert address == 0

        address = combine_address_16bit(0xFFFF, 0xFFFF)
        assert address == 0xFFFFFFFF

    def test_address_split_combine_roundtrip(self) -> None:
        """Test that split and combine are inverse operations."""
        test_addresses = [0, 0x001236E0, 0xFFFFFFFF, 0x12345678]

        for original in test_addresses:
            low, high = split_address_16bit(original)
            combined = combine_address_16bit(low, high)
            assert combined == original

    def test_validate_voltage_range_valid(self) -> None:
        """Test validating voltages within range."""
        # Should not raise
        validate_voltage_range(-2.0, -5.0, -0.2)
        validate_voltage_range(-5.0, -5.0, -0.2)
        validate_voltage_range(-0.2, -5.0, -0.2)

    def test_validate_voltage_range_invalid(self) -> None:
        """Test validating voltages outside range."""
        with pytest.raises(InvalidParameterError, match="Voltage.*out of range"):
            validate_voltage_range(-6.0, -5.0, -0.2)

        with pytest.raises(InvalidParameterError, match="Voltage.*out of range"):
            validate_voltage_range(0.0, -5.0, -0.2)

    def test_pack_bytes_to_words(self) -> None:
        """Test packing bytes into 16-bit words."""
        # Test even number of bytes
        data = bytes([0x12, 0x34, 0x56, 0x78])
        words = pack_bytes_to_words(data)
        assert words == [0x1234, 0x5678]

        # Test odd number of bytes (should pad with zero)
        data = bytes([0x12, 0x34, 0x56])
        words = pack_bytes_to_words(data)
        assert words == [0x1234, 0x5600]

        # Test empty data
        words = pack_bytes_to_words(b"")
        assert words == []

        # Test single byte
        words = pack_bytes_to_words(bytes([0xFF]))
        assert words == [0xFF00]

    def test_validate_dimensions_valid(self) -> None:
        """Test validating valid dimensions."""
        # Should not raise
        validate_dimensions(100, 200, 2048, 2048)
        validate_dimensions(2048, 2048, 2048, 2048)
        validate_dimensions(1, 1, 2048, 2048)

    def test_validate_dimensions_invalid(self) -> None:
        """Test validating invalid dimensions."""
        # Test non-positive dimensions
        with pytest.raises(InvalidParameterError, match="must be positive"):
            validate_dimensions(0, 100, 2048, 2048)

        with pytest.raises(InvalidParameterError, match="must be positive"):
            validate_dimensions(100, 0, 2048, 2048)

        with pytest.raises(InvalidParameterError, match="must be positive"):
            validate_dimensions(-1, 100, 2048, 2048)

        # Test exceeding maximum
        with pytest.raises(InvalidParameterError, match="exceed maximum"):
            validate_dimensions(2049, 100, 2048, 2048)

        with pytest.raises(InvalidParameterError, match="exceed maximum"):
            validate_dimensions(100, 2049, 2048, 2048)

    def test_validate_rectangle_valid(self) -> None:
        """Test validating valid rectangles using new dataclass approach."""
        # Should not raise
        rect = Rectangle(x=0, y=0, width=100, height=100)
        bounds = Bounds(width=1024, height=768)
        validate_rectangle(rect, bounds)

        rect = Rectangle(x=924, y=668, width=100, height=100)
        validate_rectangle(rect, bounds)

        rect = Rectangle(x=0, y=0, width=1024, height=768)
        validate_rectangle(rect, bounds)

    def test_validate_rectangle_invalid(self) -> None:
        """Test validating invalid rectangles using new dataclass approach."""
        bounds = Bounds(width=1024, height=768)

        # Test negative coordinates
        rect = Rectangle(x=-1, y=0, width=100, height=100)
        with pytest.raises(InvalidParameterError, match="must be non-negative"):
            validate_rectangle(rect, bounds)

        rect = Rectangle(x=0, y=-1, width=100, height=100)
        with pytest.raises(InvalidParameterError, match="must be non-negative"):
            validate_rectangle(rect, bounds)

        # Test exceeding panel width
        rect = Rectangle(x=925, y=0, width=100, height=100)
        with pytest.raises(InvalidParameterError, match="exceeds panel width"):
            validate_rectangle(rect, bounds)

        # Test exceeding panel height
        rect = Rectangle(x=0, y=669, width=100, height=100)
        with pytest.raises(InvalidParameterError, match="exceeds panel height"):
            validate_rectangle(rect, bounds)
