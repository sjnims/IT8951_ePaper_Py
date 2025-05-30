#!/usr/bin/env python3
"""Demonstration of progressive image loading for large images.

This example shows how to display very large images using the progressive
loading feature, which processes the image in chunks to manage memory usage.
"""

import argparse
import logging
import sys
from pathlib import Path

from PIL import Image

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode, PixelFormat


def create_large_test_image(width: int, height: int) -> Image.Image:
    """Create a large test image with gradients and patterns.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.

    Returns:
        PIL Image with test patterns.
    """
    from PIL import ImageDraw

    img = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(img)

    # Create horizontal gradient bands
    band_height = height // 10
    for i in range(10):
        y_start = i * band_height
        y_end = (i + 1) * band_height
        gray_value = int(i * 255 / 9)
        draw.rectangle([0, y_start, width, y_end], fill=gray_value)

    # Add some text markers
    for i in range(0, height, 100):
        draw.text((10, i), f"Y={i}", fill=0 if i % 200 == 0 else 128)

    # Add vertical lines every 100 pixels
    for x in range(0, width, 100):
        draw.line([(x, 0), (x, height)], fill=0, width=1)

    return img


def main() -> None:
    """Run the progressive loading demonstration."""
    parser = argparse.ArgumentParser(description="Progressive image loading demo")
    parser.add_argument(
        "vcom",
        type=float,
        help="VCOM voltage for your display (e.g., -2.0)",
    )
    parser.add_argument(
        "--image",
        type=Path,
        help="Path to image file (if not provided, creates test image)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=256,
        help="Chunk height in pixels (default: 256)",
    )
    parser.add_argument(
        "--pixel-format",
        choices=["1bpp", "2bpp", "4bpp", "8bpp"],
        default="4bpp",
        help="Pixel format (default: 4bpp)",
    )
    parser.add_argument(
        "--mode",
        choices=["init", "gc16", "gl16", "du", "a2"],
        default="gc16",
        help="Display mode (default: gc16)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Map string arguments to enums
    pixel_formats = {
        "1bpp": PixelFormat.BPP_1,
        "2bpp": PixelFormat.BPP_2,
        "4bpp": PixelFormat.BPP_4,
        "8bpp": PixelFormat.BPP_8,
    }

    display_modes = {
        "init": DisplayMode.INIT,
        "gc16": DisplayMode.GC16,
        "gl16": DisplayMode.GL16,
        "du": DisplayMode.DU,
        "a2": DisplayMode.A2,
    }

    pixel_format = pixel_formats[args.pixel_format]
    display_mode = display_modes[args.mode]

    # Initialize display
    logging.info("Initializing display...")
    display = EPaperDisplay(vcom=args.vcom)

    try:
        width, height = display.init()
        logging.info(f"Display initialized: {width}x{height}")

        # Load or create image
        if args.image and args.image.exists():
            logging.info(f"Loading image: {args.image}")
            img = Image.open(args.image).convert("L")
        else:
            # Create a large test image
            logging.info("Creating large test image...")
            img = create_large_test_image(width, height)

        # Calculate memory usage
        total_pixels = img.width * img.height
        memory_bytes = {
            PixelFormat.BPP_1: (total_pixels + 7) // 8,
            PixelFormat.BPP_2: (total_pixels + 3) // 4,
            PixelFormat.BPP_4: (total_pixels + 1) // 2,
            PixelFormat.BPP_8: total_pixels,
        }

        estimated_memory = memory_bytes[pixel_format]
        logging.info(f"Image size: {img.width}x{img.height} pixels")
        logging.info(
            f"Estimated memory usage: {estimated_memory:,} bytes "
            f"({estimated_memory / (1024 * 1024):.2f} MB)"
        )

        # Calculate chunk information
        chunk_pixels = img.width * args.chunk_size
        chunk_memory = {
            PixelFormat.BPP_1: (chunk_pixels + 7) // 8,
            PixelFormat.BPP_2: (chunk_pixels + 3) // 4,
            PixelFormat.BPP_4: (chunk_pixels + 1) // 2,
            PixelFormat.BPP_8: chunk_pixels,
        }

        chunk_mem = chunk_memory[pixel_format]
        num_chunks = (img.height + args.chunk_size - 1) // args.chunk_size

        logging.info(f"Progressive loading with {num_chunks} chunks of {args.chunk_size} pixels")
        logging.info(f"Memory per chunk: {chunk_mem:,} bytes ({chunk_mem / 1024:.1f} KB)")

        # Clear display
        logging.info("Clearing display...")
        display.clear()

        # Display image progressively
        logging.info(f"Displaying image progressively ({args.pixel_format}, {args.mode})...")
        display.display_image_progressive(
            img,
            mode=display_mode,
            pixel_format=pixel_format,
            chunk_height=args.chunk_size,
        )

        logging.info("Image displayed successfully!")

        # Compare with regular display method memory usage
        logging.info("\nComparison with regular display_image method:")
        logging.info(f"- Regular method loads entire image: {estimated_memory:,} bytes")
        logging.info(f"- Progressive method loads chunks: {chunk_mem:,} bytes per chunk")
        logging.info(
            f"- Memory reduction: {(1 - chunk_mem / estimated_memory) * 100:.1f}% "
            f"(for chunk size {args.chunk_size})"
        )

    finally:
        display.close()
        logging.info("Display closed")


if __name__ == "__main__":
    main()
