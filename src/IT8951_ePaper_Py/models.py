"""Data models for IT8951 e-paper driver."""
# ruff: noqa: PLR2004

from pydantic import BaseModel, Field, field_validator

from IT8951_ePaper_Py.constants import (
    DisplayConstants,
    DisplayMode,
    EndianType,
    PixelFormat,
    ProtocolConstants,
    Rotation,
)


class DeviceInfo(BaseModel):
    """IT8951 device information."""

    panel_width: int = Field(..., ge=1, le=DisplayConstants.MAX_WIDTH)
    panel_height: int = Field(..., ge=1, le=DisplayConstants.MAX_HEIGHT)
    memory_addr_l: int = Field(..., ge=0, le=ProtocolConstants.ADDRESS_MASK)
    memory_addr_h: int = Field(..., ge=0, le=ProtocolConstants.ADDRESS_MASK)
    fw_version: str | list[int] = Field(...)
    lut_version: str | list[int] = Field(...)

    @property
    def memory_address(self) -> int:
        """Get the full memory address."""
        return (self.memory_addr_h << (ProtocolConstants.BYTE_SHIFT * 2)) | self.memory_addr_l

    @field_validator("fw_version", "lut_version", mode="before")
    @classmethod
    def convert_version(cls, v: str | list[int]) -> str:
        """Convert version from array of uint16 to string."""
        if isinstance(v, list):
            chars: list[str] = []
            for val in v:
                if val == 0:
                    break
                chars.append(chr(val))
            return "".join(chars)
        return v


class LoadImageInfo(BaseModel):
    """Information for loading images to IT8951."""

    endian_type: EndianType = Field(default=EndianType.LITTLE)
    pixel_format: PixelFormat = Field(default=PixelFormat.BPP_8)
    rotate: Rotation = Field(default=Rotation.ROTATE_0)
    source_buffer: bytes = Field(...)
    target_memory_addr: int = Field(..., ge=0)

    @field_validator("source_buffer")
    @classmethod
    def validate_buffer(cls, v: bytes) -> bytes:
        """Validate buffer is not empty."""
        if not v:
            raise ValueError("Source buffer cannot be empty")
        return v


class AreaImageInfo(BaseModel):
    """Information for area-specific image operations."""

    x: int = Field(..., ge=0, alias="area_x")
    y: int = Field(..., ge=0, alias="area_y")
    width: int = Field(..., gt=0, alias="area_w")
    height: int = Field(..., gt=0, alias="area_h")

    @field_validator("x", "y", "width", "height", mode="before")
    @classmethod
    def validate_coordinates(cls, v: int) -> int:
        """Ensure coordinates are valid."""
        if v < 0:
            raise ValueError("Coordinates must be non-negative")
        return v


class DisplayArea(BaseModel):
    """Display area for refresh operations."""

    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    mode: DisplayMode = Field(default=DisplayMode.GC16)

    @field_validator("x", "y")
    @classmethod
    def validate_position(cls, v: int) -> int:
        """Validate position is aligned to 4 pixels."""
        if v % DisplayConstants.PIXEL_ALIGNMENT != 0:
            raise ValueError(
                f"Position must be aligned to {DisplayConstants.PIXEL_ALIGNMENT} pixels"
            )
        return v

    @field_validator("width", "height")
    @classmethod
    def validate_dimensions(cls, v: int) -> int:
        """Validate dimensions are multiples of 4."""
        if v % DisplayConstants.PIXEL_ALIGNMENT != 0:
            raise ValueError(f"Dimensions must be multiples of {DisplayConstants.PIXEL_ALIGNMENT}")
        return v


class VCOMConfig(BaseModel):
    """VCOM voltage configuration."""

    voltage: float = Field(..., ge=DisplayConstants.MIN_VCOM, le=DisplayConstants.MAX_VCOM)

    @field_validator("voltage")
    @classmethod
    def validate_voltage(cls, v: float) -> float:
        """Validate VCOM voltage is within safe range."""
        if not DisplayConstants.MIN_VCOM <= v <= DisplayConstants.MAX_VCOM:
            raise ValueError(
                f"VCOM voltage must be between {DisplayConstants.MIN_VCOM}V "
                f"and {DisplayConstants.MAX_VCOM}V"
            )
        return round(v, 2)
