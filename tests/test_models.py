"""Tests for data models."""

import pytest
from pydantic import ValidationError

from IT8951_ePaper_Py.constants import DisplayMode, EndianType, PixelFormat, Rotation
from IT8951_ePaper_Py.models import (
    AreaImageInfo,
    DeviceInfo,
    DisplayArea,
    LoadImageInfo,
    VCOMConfig,
)


class TestDeviceInfo:
    """Test DeviceInfo model."""

    def test_valid_device_info(self) -> None:
        """Test creating valid device info."""
        info = DeviceInfo(
            panel_width=1024,
            panel_height=768,
            memory_addr_l=0x1234,
            memory_addr_h=0x5678,
            fw_version="1.0.0",
            lut_version="2.0.0",
        )
        assert info.panel_width == 1024
        assert info.panel_height == 768
        assert info.memory_address == 0x56781234

    def test_version_from_array(self) -> None:
        """Test converting version from uint16 array."""
        info = DeviceInfo(
            panel_width=1024,
            panel_height=768,
            memory_addr_l=0,
            memory_addr_h=0,
            fw_version=[49, 46, 48, 46, 48, 0, 0, 0],  # "1.0.0"
            lut_version=[50, 46, 48, 46, 48, 0, 0, 0],  # "2.0.0"
        )
        assert info.fw_version == "1.0.0"
        assert info.lut_version == "2.0.0"

    def test_invalid_panel_dimensions(self) -> None:
        """Test validation of panel dimensions."""
        with pytest.raises(ValidationError):
            DeviceInfo(
                panel_width=3000,  # Too large
                panel_height=768,
                memory_addr_l=0,
                memory_addr_h=0,
                fw_version="1.0",
                lut_version="1.0",
            )

    def test_memory_address_calculation(self) -> None:
        """Test memory address calculation."""
        info = DeviceInfo(
            panel_width=1024,
            panel_height=768,
            memory_addr_l=0xABCD,
            memory_addr_h=0x1234,
            fw_version="1.0",
            lut_version="1.0",
        )
        assert info.memory_address == 0x1234ABCD


class TestLoadImageInfo:
    """Test LoadImageInfo model."""

    def test_valid_load_info(self) -> None:
        """Test creating valid load image info."""
        data = b"test data"
        info = LoadImageInfo(
            source_buffer=data,
            target_memory_addr=0x100000,
            endian_type=EndianType.LITTLE,
            pixel_format=PixelFormat.BPP_8,
            rotate=Rotation.ROTATE_90,
        )
        assert info.source_buffer == data
        assert info.target_memory_addr == 0x100000
        assert info.endian_type == EndianType.LITTLE
        assert info.pixel_format == PixelFormat.BPP_8
        assert info.rotate == Rotation.ROTATE_90

    def test_default_values(self) -> None:
        """Test default values for optional fields."""
        info = LoadImageInfo(
            source_buffer=b"data",
            target_memory_addr=0,
        )
        assert info.endian_type == EndianType.LITTLE
        assert info.pixel_format == PixelFormat.BPP_4
        assert info.rotate == Rotation.ROTATE_0

    def test_empty_buffer_validation(self) -> None:
        """Test validation rejects empty buffer."""
        with pytest.raises(ValidationError):
            LoadImageInfo(
                source_buffer=b"",
                target_memory_addr=0,
            )


class TestAreaImageInfo:
    """Test AreaImageInfo model."""

    def test_valid_area_info(self) -> None:
        """Test creating valid area info."""
        info = AreaImageInfo(
            area_x=100,
            area_y=200,
            area_w=300,
            area_h=400,
        )
        assert info.x == 100
        assert info.y == 200
        assert info.width == 300
        assert info.height == 400

    def test_negative_coordinates_rejected(self) -> None:
        """Test negative coordinates are rejected."""
        with pytest.raises(ValidationError):
            AreaImageInfo(
                area_x=-10,
                area_y=0,
                area_w=100,
                area_h=100,
            )

    def test_zero_dimensions_rejected(self) -> None:
        """Test zero dimensions are rejected."""
        with pytest.raises(ValidationError):
            AreaImageInfo(
                area_x=0,
                area_y=0,
                area_w=0,
                area_h=100,
            )


class TestDisplayArea:
    """Test DisplayArea model."""

    def test_valid_display_area(self) -> None:
        """Test creating valid display area."""
        area = DisplayArea(
            x=0,
            y=0,
            width=800,
            height=600,
            mode=DisplayMode.GC16,
        )
        assert area.x == 0
        assert area.y == 0
        assert area.width == 800
        assert area.height == 600
        assert area.mode == DisplayMode.GC16

    def test_alignment_validation(self) -> None:
        """Test position and dimension alignment validation."""
        with pytest.raises(ValidationError, match="aligned to 4 pixels"):
            DisplayArea(
                x=1,  # Not aligned to 4
                y=0,
                width=800,
                height=600,
            )

        with pytest.raises(ValidationError, match="multiples of 4"):
            DisplayArea(
                x=0,
                y=0,
                width=801,  # Not multiple of 4
                height=600,
            )

    def test_default_mode(self) -> None:
        """Test default display mode."""
        area = DisplayArea(
            x=0,
            y=0,
            width=800,
            height=600,
        )
        assert area.mode == DisplayMode.GC16


class TestVCOMConfig:
    """Test VCOMConfig model."""

    def test_valid_vcom(self) -> None:
        """Test creating valid VCOM config."""
        config = VCOMConfig(voltage=-2.5)
        assert config.voltage == -2.5

    def test_vcom_range_validation(self) -> None:
        """Test VCOM voltage range validation."""
        with pytest.raises(ValidationError):
            VCOMConfig(voltage=-6.0)  # Too low

        with pytest.raises(ValidationError):
            VCOMConfig(voltage=0.0)  # Too high

    def test_vcom_rounding(self) -> None:
        """Test VCOM voltage is rounded to 2 decimal places."""
        config = VCOMConfig(voltage=-2.567)
        assert config.voltage == -2.57
