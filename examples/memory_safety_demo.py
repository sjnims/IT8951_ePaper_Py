#!/usr/bin/env python3
"""Demonstration of memory safety features.

This example shows how the driver's memory safety features work,
including warnings, error handling, and progressive loading.
"""

import argparse
import logging
import sys
from pathlib import Path

from PIL import Image, ImageDraw

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode, MemoryConstants, PixelFormat
from IT8951_ePaper_Py.exceptions import IT8951MemoryError


def create_test_image(width: int, height: int, pattern: str = "gradient") -> Image.Image:
    """Create a test image with specified pattern.

    Args:
        width: Image width.
        height: Image height.
        pattern: Pattern type ("gradient", "checkerboard", "text").

    Returns:
        PIL Image.
    """
    img = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(img)

    if pattern == "gradient":
        # Horizontal gradient
        for x in range(width):
            gray = int(x * 255 / width)
            draw.line([(x, 0), (x, height)], fill=gray)

    elif pattern == "checkerboard":
        # Checkerboard pattern
        square_size = 50
        for y in range(0, height, square_size):
            for x in range(0, width, square_size):
                if (x // square_size + y // square_size) % 2:
                    draw.rectangle([x, y, x + square_size, y + square_size], fill=0)

    elif pattern == "text":
        # Text pattern
        for y in range(0, height, 20):
            draw.text((10, y), f"Line {y // 20}: Memory safety demo", fill=0)

    return img


def demonstrate_memory_warnings(display: EPaperDisplay) -> None:
    """Demonstrate memory usage warnings."""
    logging.info("\n=== Memory Warning Demonstration ===")

    # Create an image that will trigger a warning
    # We need to create an image that uses more than WARNING_THRESHOLD_BYTES
    # at the specified pixel format

    # Calculate size needed to trigger warning at 8bpp
    warning_pixels = MemoryConstants.WARNING_THRESHOLD_BYTES + 1
    # Make it square
    size = int(warning_pixels**0.5)

    logging.info(f"Creating {size}x{size} image ({warning_pixels:,} bytes at 8bpp)")
    img = create_test_image(size, size, "gradient")

    logging.info("Displaying with 8bpp (should trigger warning)...")
    display.display_image(img, pixel_format=PixelFormat.BPP_8)

    logging.info("Displaying with 4bpp (may not trigger warning)...")
    display.display_image(img, pixel_format=PixelFormat.BPP_4)


def demonstrate_memory_error(display: EPaperDisplay) -> None:
    """Demonstrate memory error handling."""
    logging.info("\n=== Memory Error Demonstration ===")

    # Try to create an image that exceeds safe memory limit
    safe_pixels = MemoryConstants.SAFE_IMAGE_MEMORY_BYTES + 1
    size = int(safe_pixels**0.5)

    logging.info(f"Attempting to display {size}x{size} image")
    logging.info(f"This would use {safe_pixels:,} bytes, exceeding safe limit")

    try:
        img = create_test_image(size, size, "checkerboard")
        display.display_image(img, pixel_format=PixelFormat.BPP_8)
    except IT8951MemoryError as e:
        logging.error(f"Caught expected memory error: {e}")
        logging.info("This is expected behavior - the driver prevented unsafe operation")


def demonstrate_progressive_loading(display: EPaperDisplay) -> None:
    """Demonstrate progressive loading for large images."""
    logging.info("\n=== Progressive Loading Demonstration ===")

    # Create a large image
    width, height = display.width, display.height
    logging.info(f"Creating full-screen image ({width}x{height})")

    img = create_test_image(width, height, "text")

    # Calculate memory usage
    total_pixels = width * height
    memory_usage = {
        PixelFormat.BPP_8: total_pixels,
        PixelFormat.BPP_4: (total_pixels + 1) // 2,
        PixelFormat.BPP_2: (total_pixels + 3) // 4,
        PixelFormat.BPP_1: (total_pixels + 7) // 8,
    }

    for fmt, bytes_used in memory_usage.items():
        name = {
            PixelFormat.BPP_8: "8bpp",
            PixelFormat.BPP_4: "4bpp",
            PixelFormat.BPP_2: "2bpp",
            PixelFormat.BPP_1: "1bpp",
        }[fmt]
        logging.info(f"  {name}: {bytes_used:,} bytes ({bytes_used / 1024 / 1024:.1f} MB)")

    # Display using progressive loading
    logging.info("\nDisplaying with progressive loading (256-pixel chunks)...")
    display.display_image_progressive(
        img, pixel_format=PixelFormat.BPP_4, chunk_height=256, mode=DisplayMode.GC16
    )

    # Show memory savings
    chunk_pixels = width * 256
    chunk_memory = (chunk_pixels + 1) // 2  # 4bpp
    total_memory = memory_usage[PixelFormat.BPP_4]

    logging.info("\nMemory usage comparison:")
    logging.info(f"  Regular method: {total_memory:,} bytes loaded at once")
    logging.info(f"  Progressive method: {chunk_memory:,} bytes per chunk")
    logging.info(f"  Memory reduction: {(1 - chunk_memory / total_memory) * 100:.1f}%")


def demonstrate_size_limits(display: EPaperDisplay) -> None:
    """Demonstrate image size limits."""
    logging.info("\n=== Size Limit Demonstration ===")

    # Try to create an image exceeding max dimensions
    logging.info("Attempting to display 3000x3000 image (exceeds 2048x2048 limit)...")

    try:
        img = Image.new("L", (3000, 3000), color=128)
        display.display_image(img)
    except IT8951MemoryError as e:
        logging.error(f"Caught expected error: {e}")
        logging.info("Driver correctly rejected oversized image")


def main() -> None:
    """Run memory safety demonstrations."""
    parser = argparse.ArgumentParser(description="Memory safety features demo")
    parser.add_argument(
        "vcom",
        type=float,
        help="VCOM voltage for your display (e.g., -2.0)",
    )
    parser.add_argument(
        "--demo",
        choices=["all", "warnings", "errors", "progressive", "limits"],
        default="all",
        help="Which demo to run (default: all)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Initialize display
    logging.info("Initializing display...")
    logging.info("Note: VCOM is now a required parameter for safety")
    display = EPaperDisplay(vcom=args.vcom)

    try:
        width, height = display.init()
        logging.info(f"Display initialized: {width}x{height}")

        # Clear display
        logging.info("Clearing display...")
        display.clear()

        # Run demos
        if args.demo in ["all", "warnings"]:
            demonstrate_memory_warnings(display)

        if args.demo in ["all", "errors"]:
            demonstrate_memory_error(display)

        if args.demo in ["all", "progressive"]:
            demonstrate_progressive_loading(display)

        if args.demo in ["all", "limits"]:
            demonstrate_size_limits(display)

        logging.info("\n=== Demo Complete ===")
        logging.info("Memory safety features help prevent:")
        logging.info("  - Out of memory errors")
        logging.info("  - Display hardware damage")
        logging.info("  - Poor performance from excessive memory use")

    finally:
        display.close()
        logging.info("Display closed")


if __name__ == "__main__":
    main()
