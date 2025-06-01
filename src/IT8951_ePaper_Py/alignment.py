"""Alignment utilities for IT8951 e-paper driver.

This module provides shared alignment functionality to ensure coordinates
and dimensions meet hardware requirements for different pixel formats.

The IT8951 controller has specific alignment requirements that depend on the
pixel format being used. These requirements are critical for proper display
operation and avoiding visual artifacts or hardware errors.

Alignment Requirements by Format:
    - 1bpp: 32-pixel (4-byte) alignment for x-coordinate and width
    - 2/4/8bpp: 4-pixel alignment for all parameters

The alignment ensures efficient memory access and prevents display corruption
that can occur when data boundaries don't match hardware expectations.
"""

from collections.abc import Callable

from IT8951_ePaper_Py.constants import DisplayConstants, PixelFormat


def get_alignment_boundary(pixel_format: PixelFormat | None = None) -> int:
    """Get the required alignment boundary for a given pixel format.

    Different pixel formats have different alignment requirements due to how
    the IT8951 controller packs pixel data into memory. This function returns
    the minimum pixel boundary that coordinates and dimensions must align to.

    Args:
        pixel_format: Pixel format to check. If None, defaults to BPP_4
            which is the most commonly used format.

    Returns:
        Alignment boundary in pixels. Will be either 32 (for 1bpp) or 4
        (for all other formats).

    Examples:
        >>> get_alignment_boundary(PixelFormat.BPP_1)  # Binary images
        32
        >>> get_alignment_boundary(PixelFormat.BPP_4)  # Grayscale
        4
        >>> get_alignment_boundary()  # Default
        4
    """
    if pixel_format is None:
        pixel_format = PixelFormat.BPP_4

    # 1bpp requires 32-bit (32 pixel) alignment per wiki documentation
    if pixel_format == PixelFormat.BPP_1:
        return DisplayConstants.PIXEL_ALIGNMENT_1BPP
    return DisplayConstants.PIXEL_ALIGNMENT


def align_coordinate(coord: int, pixel_format: PixelFormat | None = None) -> int:
    """Align coordinate to appropriate boundary based on pixel format.

    Coordinates (x, y) must be aligned to specific boundaries to ensure the
    hardware can properly address the display memory. This function rounds
    down to the nearest valid boundary.

    Args:
        coord: Input coordinate (x or y position) to align.
        pixel_format: Pixel format determining alignment rules.
            If None, defaults to BPP_4.

    Returns:
        Aligned coordinate rounded down to the nearest boundary.
        For example, with 4-pixel alignment: 13 -> 12, 16 -> 16.

    Examples:
        >>> align_coordinate(13, PixelFormat.BPP_4)  # 4-pixel boundary
        12
        >>> align_coordinate(35, PixelFormat.BPP_1)  # 32-pixel boundary
        32
        >>> align_coordinate(64, PixelFormat.BPP_1)  # Already aligned
        64

    Note:
        Rounding down means some pixels on the left/top edge may be
        cropped if the original coordinate wasn't aligned.
    """
    alignment = get_alignment_boundary(pixel_format)
    return (coord // alignment) * alignment


def align_dimension(dim: int, pixel_format: PixelFormat | None = None) -> int:
    """Align dimension to appropriate multiple based on pixel format.

    Dimensions (width, height) must be multiples of the alignment boundary
    to ensure complete pixel data can be transmitted. This function rounds
    up to include all pixels.

    Args:
        dim: Input dimension (width or height) to align.
        pixel_format: Pixel format determining alignment rules.
            If None, defaults to BPP_4.

    Returns:
        Aligned dimension rounded up to the nearest boundary.
        For example, with 4-pixel alignment: 13 -> 16, 16 -> 16.

    Examples:
        >>> align_dimension(13, PixelFormat.BPP_4)  # 4-pixel boundary
        16
        >>> align_dimension(30, PixelFormat.BPP_1)  # 32-pixel boundary
        32
        >>> align_dimension(64, PixelFormat.BPP_1)  # Already aligned
        64

    Note:
        Rounding up means the display area may be larger than the
        original image, with padding added on the right/bottom edges.
    """
    alignment = get_alignment_boundary(pixel_format)
    return ((dim + alignment - 1) // alignment) * alignment


def get_alignment_description(pixel_format: PixelFormat | None = None) -> str:
    """Get human-readable description of alignment requirements.

    This function provides user-friendly descriptions of alignment
    requirements for error messages and warnings.

    Args:
        pixel_format: Pixel format to describe. If None, defaults to BPP_4.

    Returns:
        Human-readable description of the alignment requirement.
        Includes byte alignment info for 1bpp since it's less intuitive.

    Examples:
        >>> get_alignment_description(PixelFormat.BPP_1)
        '32-pixel (4-byte)'
        >>> get_alignment_description(PixelFormat.BPP_4)
        '4-pixel'
        >>> get_alignment_description()  # Default
        '4-pixel'
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

    Checks if the given display area meets alignment requirements and
    generates helpful warnings for any issues found. This helps users
    understand why their display operations might be adjusted.

    Args:
        x: X coordinate of the display area.
        y: Y coordinate of the display area.
        width: Width of the display area in pixels.
        height: Height of the display area in pixels.
        pixel_format: Pixel format determining alignment rules.
            If None, defaults to BPP_4.

    Returns:
        A tuple containing:
        - is_valid: True if all parameters are properly aligned, False otherwise.
        - warnings: List of warning messages describing alignment issues.
            Empty list if no issues found.

    Examples:
        >>> validate_alignment(0, 0, 100, 100, PixelFormat.BPP_4)
        (True, [])

        >>> is_valid, warnings = validate_alignment(13, 0, 100, 100, PixelFormat.BPP_4)
        >>> is_valid
        False
        >>> warnings[0]
        'X coordinate 13 not aligned to 4-pixel boundary. Will be adjusted to 12'

        >>> is_valid, warnings = validate_alignment(10, 10, 50, 50, PixelFormat.BPP_1)
        >>> len(warnings)  # Multiple alignment issues
        4
        >>> warnings[0].startswith('Note: 1bpp mode requires')
        True

    Note:
        The function checks all parameters even if some are misaligned,
        providing a complete list of issues rather than stopping at the
        first problem.
    """
    if pixel_format is None:
        pixel_format = PixelFormat.BPP_4

    warnings = _check_parameter_alignment(x, y, width, height, pixel_format)

    # Add special warning for 1bpp if there are alignment issues
    if pixel_format == PixelFormat.BPP_1 and warnings:
        warnings.insert(0, _get_1bpp_warning())

    return (len(warnings) == 0, warnings)


def _check_parameter_alignment(
    x: int, y: int, width: int, height: int, pixel_format: PixelFormat
) -> list[str]:
    """Check alignment for all parameters and return warnings."""
    warnings: list[str] = []
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
        warning = _check_single_parameter(
            param_name, value, align_func, pixel_format, alignment, alignment_desc
        )
        if warning:
            warnings.append(warning)

    return warnings


def _check_single_parameter(  # noqa: PLR0913
    param_name: str,
    value: int,
    align_func: Callable[[int, PixelFormat], int],
    pixel_format: PixelFormat,
    alignment: int,
    alignment_desc: str,
) -> str | None:
    """Check a single parameter alignment and return warning if needed."""
    if value % alignment == 0:
        return None

    aligned_value = align_func(value, pixel_format)
    return (
        f"{param_name} {value} not aligned to {alignment_desc} boundary. "
        f"Will be adjusted to {aligned_value}"
    )


def _get_1bpp_warning() -> str:
    """Get the special warning message for 1bpp mode."""
    return (
        "Note: 1bpp mode requires strict 32-pixel alignment on some models. "
        "Image may be cropped or padded to meet requirements."
    )
