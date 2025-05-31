"""Alignment utilities for IT8951 e-paper driver.

This module provides shared alignment functionality to ensure coordinates
and dimensions meet hardware requirements for different pixel formats.
"""

from IT8951_ePaper_Py.constants import DisplayConstants, PixelFormat


def get_alignment_boundary(pixel_format: PixelFormat | None = None) -> int:
    """Get the required alignment boundary for a given pixel format.

    Args:
        pixel_format: Pixel format (defaults to BPP_4).

    Returns:
        Alignment boundary in pixels.
    """
    if pixel_format is None:
        pixel_format = PixelFormat.BPP_4

    # 1bpp requires 32-bit (32 pixel) alignment per wiki documentation
    if pixel_format == PixelFormat.BPP_1:
        return DisplayConstants.PIXEL_ALIGNMENT_1BPP
    return DisplayConstants.PIXEL_ALIGNMENT


def align_coordinate(coord: int, pixel_format: PixelFormat | None = None) -> int:
    """Align coordinate to appropriate boundary based on pixel format.

    Args:
        coord: Input coordinate.
        pixel_format: Pixel format (defaults to BPP_4).

    Returns:
        Aligned coordinate (rounded down to boundary).
    """
    alignment = get_alignment_boundary(pixel_format)
    return (coord // alignment) * alignment


def align_dimension(dim: int, pixel_format: PixelFormat | None = None) -> int:
    """Align dimension to appropriate multiple based on pixel format.

    Args:
        dim: Input dimension.
        pixel_format: Pixel format (defaults to BPP_4).

    Returns:
        Aligned dimension (rounded up to boundary).
    """
    alignment = get_alignment_boundary(pixel_format)
    return ((dim + alignment - 1) // alignment) * alignment


def get_alignment_description(pixel_format: PixelFormat | None = None) -> str:
    """Get human-readable description of alignment requirements.

    Args:
        pixel_format: Pixel format (defaults to BPP_4).

    Returns:
        Description string like "32-pixel (4-byte)" or "4-pixel".
    """
    if pixel_format is None:
        pixel_format = PixelFormat.BPP_4

    if pixel_format == PixelFormat.BPP_1:
        return "32-pixel (4-byte)"
    return "4-pixel"


def validate_alignment(
    x: int, y: int, width: int, height: int, pixel_format: PixelFormat | None = None
) -> tuple[bool, list[str]]:
    """Validate alignment requirements for display operation.

    Args:
        x: X coordinate.
        y: Y coordinate.
        width: Image width.
        height: Image height.
        pixel_format: Pixel format (defaults to BPP_4).

    Returns:
        Tuple of (is_valid, warnings) where warnings contains any alignment issues.
    """
    warnings: list[str] = []

    if pixel_format is None:
        pixel_format = PixelFormat.BPP_4

    alignment = get_alignment_boundary(pixel_format)
    alignment_desc = get_alignment_description(pixel_format)

    # Check all parameters
    params = [
        ("X coordinate", x, align_coordinate),
        ("Y coordinate", y, align_coordinate),
        ("Width", width, align_dimension),
        ("Height", height, align_dimension),
    ]

    for param_name, value, align_func in params:
        if value % alignment != 0:
            aligned_value = align_func(value, pixel_format)
            warnings.append(
                f"{param_name} {value} not aligned to {alignment_desc} boundary. "
                f"Will be adjusted to {aligned_value}"
            )

    # Special warning for 1bpp
    if pixel_format == PixelFormat.BPP_1 and warnings:
        warnings.insert(
            0,
            "Note: 1bpp mode requires strict 32-pixel alignment on some models. "
            "Image may be cropped or padded to meet requirements.",
        )

    return (len(warnings) == 0, warnings)
