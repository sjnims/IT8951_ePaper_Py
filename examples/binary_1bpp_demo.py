#!/usr/bin/env python3
"""Demonstrate 1bpp binary display mode for text, QR codes, and line art.

This example shows how to use 1bpp mode for maximum performance with binary content.
1bpp mode is ideal for:
- Text display
- QR codes and barcodes
- Line drawings and diagrams
- Simple UI elements

Performance benefits:
- 8x less data to transfer compared to 8bpp
- 2x less data compared to 4bpp
- Fastest possible refresh rates
"""

import argparse
import logging

from PIL import Image, ImageDraw, ImageFont

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode, PixelFormat

logger = logging.getLogger(__name__)


def create_text_image(width: int, height: int) -> Image.Image:
    """Create a sample text image for binary display."""
    img = Image.new("L", (width, height), 255)  # White background
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fall back to default if not available
    try:
        font_size = 48
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    # Draw some text
    text = "1bpp Binary Mode Demo"
    draw.text((50, 50), text, fill=0, font=font)

    # Draw smaller text
    try:
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except Exception:
        small_font = ImageFont.load_default()

    lines = [
        "• Ultra-fast refresh rates",
        "• Perfect for text display",
        "• 8x less data than 8bpp",
        "• Ideal for e-readers",
    ]

    y_offset = 150
    for line in lines:
        draw.text((50, y_offset), line, fill=0, font=small_font)
        y_offset += 40

    return img


def create_qr_code(size: int = 400) -> Image.Image:
    """Create a sample QR code pattern (simplified for demo)."""
    img = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(img)

    # Draw a simplified QR-like pattern
    # Real QR codes would use a proper QR library
    module_size = 10
    pattern = [
        [1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1],
        [1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1],
        [1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1],
    ]

    # Draw the pattern
    for y, row in enumerate(pattern):
        for x, module in enumerate(row):
            if module:
                draw.rectangle(
                    [
                        x * module_size,
                        y * module_size,
                        (x + 1) * module_size - 1,
                        (y + 1) * module_size - 1,
                    ],
                    fill=0,
                )

    # Add text below
    draw.text((10, size - 30), "QR codes render perfectly in 1bpp", fill=0)

    return img


def create_line_art(width: int, height: int) -> Image.Image:
    """Create sample line art and diagrams."""
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    # Draw geometric shapes
    draw.rectangle([50, 50, 200, 150], outline=0, width=3)
    draw.ellipse([250, 50, 400, 150], outline=0, width=3)
    draw.polygon([(500, 150), (450, 50), (550, 50)], outline=0, width=3)

    # Draw a simple chart
    draw.line([(50, 250), (50, 400), (300, 400)], fill=0, width=2)

    # Draw bars
    bar_data = [80, 120, 60, 140, 100]
    bar_width = 40
    for i, bar_height in enumerate(bar_data):
        x = 70 + i * (bar_width + 10)
        draw.rectangle([x, 400 - bar_height, x + bar_width, 400], fill=0)

    # Add labels
    draw.text((50, 420), "Line art and charts work great in 1bpp", fill=0)

    return img


def main() -> None:
    """Run the 1bpp binary mode demo."""
    parser = argparse.ArgumentParser(description="1bpp binary display mode demo")
    parser.add_argument("vcom", type=float, help="VCOM voltage (e.g., -2.0)")
    parser.add_argument(
        "--mode",
        choices=["text", "qr", "art", "all"],
        default="all",
        help="Demo mode to display",
    )
    parser.add_argument(
        "--display-mode",
        choices=["GC16", "DU", "A2"],
        default="A2",
        help="Display update mode (A2 recommended for 1bpp)",
    )
    args = parser.parse_args()

    # Enable debug logging to see performance metrics
    logging.basicConfig(level=logging.DEBUG)

    print(f"Initializing display with VCOM={args.vcom}V...")
    display = EPaperDisplay(vcom=args.vcom)

    try:
        width, height = display.init()
        print(f"Display initialized: {width}x{height}")

        # Map display mode string to enum
        mode_map = {
            "GC16": DisplayMode.GC16,
            "DU": DisplayMode.DU,
            "A2": DisplayMode.A2,
        }
        display_mode = mode_map[args.display_mode]

        if args.mode in {"text", "all"}:
            print("\n=== Displaying text in 1bpp mode ===")
            print("Watch for the fast refresh rate!")
            text_img = create_text_image(width, height)
            display.display_image(text_img, mode=display_mode, pixel_format=PixelFormat.BPP_1)

            if args.mode == "all":
                input("\nPress Enter to continue to QR code demo...")

        if args.mode in {"qr", "all"}:
            print("\n=== Displaying QR code pattern in 1bpp mode ===")
            print("Binary patterns are perfect for 1bpp")
            qr_img = create_qr_code(min(width, height) - 100)
            # Center the QR code
            x = (width - qr_img.width) // 2
            y = (height - qr_img.height) // 2
            display.clear()
            display.display_image(
                qr_img, x=x, y=y, mode=display_mode, pixel_format=PixelFormat.BPP_1
            )

            if args.mode == "all":
                input("\nPress Enter to continue to line art demo...")

        if args.mode in {"art", "all"}:
            print("\n=== Displaying line art in 1bpp mode ===")
            print("Diagrams and charts render crisply")
            art_img = create_line_art(width, height)
            display.display_image(art_img, mode=display_mode, pixel_format=PixelFormat.BPP_1)

        print("\n=== Performance Benefits of 1bpp ===")
        print("• Data size: 1/8th of 8bpp, 1/2 of 4bpp")
        print("• Fastest possible transfer times")
        print("• Perfect for text-heavy applications")
        print(f"• Best with {display_mode.name} mode for binary content")

        if display_mode == DisplayMode.A2:
            print("\nNote: A2 mode is ideal for 1bpp as it's already binary")

    finally:
        display.close()
        print("\nDisplay closed.")


if __name__ == "__main__":
    main()
