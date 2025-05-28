"""Data models for IT8951 e-paper driver.

This module provides Pydantic models for type-safe data structures used throughout
the IT8951 driver. All models include validation to ensure data integrity.

Examples:
    Creating device info::

        device_info = DeviceInfo(
            panel_width=1872,
            panel_height=1404,
            memory_addr_l=0x36E0,
            memory_addr_h=0x12,
            fw_version="V_SWv1.0.0_6O",
            lut_version="M841"
        )
"""
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
    """IT8951 device information.

    Contains hardware specifications and firmware details retrieved from the IT8951
    controller during initialization.

    Attributes:
        panel_width: Display panel width in pixels (1-2048).
        panel_height: Display panel height in pixels (1-2048).
        memory_addr_l: Lower 16 bits of image buffer memory address.
        memory_addr_h: Upper 16 bits of image buffer memory address.
        fw_version: Firmware version string or raw version data.
        lut_version: Look-up table version string or raw version data.
    """

    panel_width: int = Field(..., ge=1, le=DisplayConstants.MAX_WIDTH)
    panel_height: int = Field(..., ge=1, le=DisplayConstants.MAX_HEIGHT)
    memory_addr_l: int = Field(..., ge=0, le=ProtocolConstants.ADDRESS_MASK)
    memory_addr_h: int = Field(..., ge=0, le=ProtocolConstants.ADDRESS_MASK)
    fw_version: str | list[int] = Field(...)
    lut_version: str | list[int] = Field(...)

    @property
    def memory_address(self) -> int:
        """Get the full 32-bit memory address.

        Combines the high and low 16-bit address components into a single
        32-bit address value.

        Returns:
            int: Full 32-bit memory address for the image buffer.
        """
        return (self.memory_addr_h << (ProtocolConstants.BYTE_SHIFT * 2)) | self.memory_addr_l

    @field_validator("fw_version", "lut_version", mode="before")
    @classmethod
    def convert_version(cls, v: str | list[int]) -> str:
        """Convert version from array of uint16 to string.

        The IT8951 returns version strings as arrays of 16-bit integers.
        This validator converts them to readable strings.

        Args:
            v: Version data as string or list of integers.

        Returns:
            str: Version as a readable string.

        Raises:
            ValueError: If version data is invalid.
        """
        if isinstance(v, list):
            chars: list[str] = []
            for val in v:
                if val == 0:
                    break
                chars.append(chr(val))
            return "".join(chars)
        return v


class LoadImageInfo(BaseModel):
    """Information for loading images to IT8951.

    Encapsulates all parameters needed for the IT8951 load image command,
    including pixel format, rotation, and memory addressing.

    Attributes:
        endian_type: Byte order for pixel data (default: LITTLE).
        pixel_format: Bits per pixel format (default: BPP_8).
        rotate: Image rotation in 90° increments (default: ROTATE_0).
        source_buffer: Raw pixel data as bytes.
        target_memory_addr: Target address in controller memory.
    """

    endian_type: EndianType = Field(default=EndianType.LITTLE)
    pixel_format: PixelFormat = Field(default=PixelFormat.BPP_8)
    rotate: Rotation = Field(default=Rotation.ROTATE_0)
    source_buffer: bytes = Field(...)
    target_memory_addr: int = Field(..., ge=0)

    @field_validator("source_buffer")
    @classmethod
    def validate_buffer(cls, v: bytes) -> bytes:
        """Validate buffer is not empty.

        Args:
            v: Source buffer bytes to validate.

        Returns:
            bytes: Validated buffer data.

        Raises:
            ValueError: If buffer is empty.
        """
        if not v:
            raise ValueError("Source buffer cannot be empty")
        return v


class AreaImageInfo(BaseModel):
    """Information for area-specific image operations.

    Defines a rectangular area for partial image updates. Supports both
    standard field names and IT8951 protocol aliases.

    Attributes:
        x: X-coordinate of top-left corner (alias: area_x).
        y: Y-coordinate of top-left corner (alias: area_y).
        width: Area width in pixels (alias: area_w).
        height: Area height in pixels (alias: area_h).
    """

    x: int = Field(..., ge=0, alias="area_x")
    y: int = Field(..., ge=0, alias="area_y")
    width: int = Field(..., gt=0, alias="area_w")
    height: int = Field(..., gt=0, alias="area_h")

    @field_validator("x", "y", "width", "height", mode="before")
    @classmethod
    def validate_coordinates(cls, v: int) -> int:
        """Ensure coordinates are valid.

        Args:
            v: Coordinate or dimension value to validate.

        Returns:
            int: Validated value.

        Raises:
            ValueError: If value is negative.
        """
        if v < 0:
            raise ValueError("Coordinates must be non-negative")
        return v


class DisplayArea(BaseModel):
    """Display area for refresh operations.

    Defines a rectangular area to be refreshed on the e-paper display.
    All coordinates and dimensions must be aligned to 4-pixel boundaries
    due to IT8951 hardware requirements.

    Attributes:
        x: X-coordinate of top-left corner (must be multiple of 4).
        y: Y-coordinate of top-left corner (must be multiple of 4).
        width: Area width in pixels (must be multiple of 4).
        height: Area height in pixels (must be multiple of 4).
        mode: Display refresh mode (default: GC16).
    """

    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    mode: DisplayMode = Field(default=DisplayMode.GC16)

    @field_validator("x", "y")
    @classmethod
    def validate_position(cls, v: int) -> int:
        """Validate position is aligned to 4 pixels.

        The IT8951 requires all coordinates to be multiples of 4.

        Args:
            v: Position coordinate to validate.

        Returns:
            int: Validated position.

        Raises:
            ValueError: If position is not aligned to 4 pixels.
        """
        if v % DisplayConstants.PIXEL_ALIGNMENT != 0:
            raise ValueError(
                f"Position must be aligned to {DisplayConstants.PIXEL_ALIGNMENT} pixels"
            )
        return v

    @field_validator("width", "height")
    @classmethod
    def validate_dimensions(cls, v: int) -> int:
        """Validate dimensions are multiples of 4.

        The IT8951 requires all dimensions to be multiples of 4.

        Args:
            v: Dimension value to validate.

        Returns:
            int: Validated dimension.

        Raises:
            ValueError: If dimension is not a multiple of 4.
        """
        if v % DisplayConstants.PIXEL_ALIGNMENT != 0:
            raise ValueError(f"Dimensions must be multiples of {DisplayConstants.PIXEL_ALIGNMENT}")
        return v


class VCOMConfig(BaseModel):
    """VCOM voltage configuration.

    Encapsulates the VCOM (common voltage) setting for the e-paper display.
    VCOM must be set correctly for proper display quality and to prevent damage.

    Attributes:
        voltage: VCOM voltage in volts (typically negative, -3.0 to -0.1V).
    """

    voltage: float = Field(..., ge=DisplayConstants.MIN_VCOM, le=DisplayConstants.MAX_VCOM)

    @field_validator("voltage")
    @classmethod
    def validate_voltage(cls, v: float) -> float:
        """Validate VCOM voltage is within safe range.

        Ensures VCOM is within the safe operating range to prevent
        display damage. Also rounds to 2 decimal places.

        Args:
            v: VCOM voltage to validate.

        Returns:
            float: Validated and rounded voltage.

        Raises:
            ValueError: If voltage is outside safe range.
        """
        if not DisplayConstants.MIN_VCOM <= v <= DisplayConstants.MAX_VCOM:
            raise ValueError(
                f"VCOM voltage must be between {DisplayConstants.MIN_VCOM}V "
                f"and {DisplayConstants.MAX_VCOM}V"
            )
        return round(v, 2)
