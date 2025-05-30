#!/usr/bin/env python3
"""Demonstrate 2bpp (2 bits per pixel) mode for 4-level grayscale.

This example shows how to use 2bpp mode for simple graphics with 4 gray levels.
2bpp mode is ideal for:
- Simple UI elements with limited shading
- Icons and symbols
- Basic charts and graphs
- Status displays with multiple states

Performance benefits:
- 4x less data than 8bpp
- 2x less data than 4bpp
- Good balance between quality and speed for simple graphics
"""

import argparse
import logging
from collections.abc import Callable

from PIL import Image, ImageDraw, ImageFont

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode, PixelFormat

logger = logging.getLogger(__name__)


def create_grayscale_palette() -> Image.Image:
    """Create a test pattern showing 4 grayscale levels."""
    width, height = 800, 200
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    # The 4 levels in 2bpp mode (after bit shifting)
    levels = [0, 85, 170, 255]  # Black, dark gray, light gray, white

    box_width = width // 4
    for i, level in enumerate(levels):
        x = i * box_width
        draw.rectangle([x, 0, x + box_width, height], fill=level)

    # Add labels
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except Exception:
        font = ImageFont.load_default()

    labels = ["Black (0)", "Dark (85)", "Light (170)", "White (255)"]
    for i, label in enumerate(labels):
        x = i * box_width + 10
        # Use contrasting color for text
        color = 255 if i < 2 else 0
        draw.text((x, height - 40), label, fill=color, font=font)

    return img


def create_icon_grid(size: int = 400) -> Image.Image:
    """Create a grid of simple icons using 4 gray levels."""
    img = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(img)

    # Icon size and grid
    icon_size = 80
    padding = 20
    icons_per_row = size // (icon_size + padding)

    # Define simple icons using the 4 gray levels
    icons: list[Callable[[int, int], list[None]]] = [
        # Home icon
        lambda x, y: [
            draw.polygon([(x + 40, y + 20), (x + 20, y + 40), (x + 60, y + 40)], fill=0),
            draw.rectangle([x + 30, y + 40, x + 50, y + 60], fill=85),
            draw.rectangle([x + 35, y + 50, x + 45, y + 60], fill=170),
        ],
        # Settings gear
        lambda x, y: [
            draw.ellipse([x + 25, y + 25, x + 55, y + 55], fill=85, outline=0),
            draw.ellipse([x + 35, y + 35, x + 45, y + 45], fill=255),
        ],
        # Battery indicator
        lambda x, y: [
            draw.rectangle([x + 20, y + 30, x + 55, y + 50], fill=255, outline=0),
            draw.rectangle([x + 55, y + 35, x + 60, y + 45], fill=0),
            draw.rectangle([x + 25, y + 35, x + 40, y + 45], fill=85),  # Charge level
        ],
        # Signal bars
        lambda x, y: [
            draw.rectangle([x + 20, y + 45, x + 25, y + 55], fill=170),
            draw.rectangle([x + 30, y + 35, x + 35, y + 55], fill=85),
            draw.rectangle([x + 40, y + 25, x + 45, y + 55], fill=0),
            draw.rectangle([x + 50, y + 35, x + 55, y + 55], fill=170),
        ],
    ]

    # Draw icons in grid
    for i, icon_func in enumerate(icons * 4):  # Repeat to fill grid
        row = i // icons_per_row
        col = i % icons_per_row

        if row >= icons_per_row:
            break

        x = col * (icon_size + padding) + padding
        y = row * (icon_size + padding) + padding

        # Draw icon background
        draw.rectangle([x, y, x + icon_size, y + icon_size], fill=255, outline=170)

        # Draw icon
        icon_func(x, y)

    return img


def create_chart(width: int, height: int) -> Image.Image:
    """Create a simple bar chart with 4 gray levels."""
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    # Chart title
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    draw.text((20, 20), "2bpp Chart Demo - 4 Gray Levels", fill=0, font=font)

    # Chart area
    chart_x = 50
    chart_y = 80
    chart_width = width - 100
    chart_height = height - 150

    # Draw axes
    draw.line(
        [(chart_x, chart_y + chart_height), (chart_x + chart_width, chart_y + chart_height)],
        fill=0,
        width=2,
    )
    draw.line([(chart_x, chart_y), (chart_x, chart_y + chart_height)], fill=0, width=2)

    # Data for bars (using different gray levels)
    data = [
        ("Q1", 0.8, 0),  # Black
        ("Q2", 0.6, 85),  # Dark gray
        ("Q3", 0.9, 170),  # Light gray
        ("Q4", 0.7, 85),  # Dark gray
    ]

    bar_width = chart_width // (len(data) * 2)

    for i, (label, value, color) in enumerate(data):
        x = chart_x + (i * 2 + 1) * bar_width
        bar_height = int(value * chart_height)
        y = chart_y + chart_height - bar_height

        # Draw bar
        draw.rectangle([x, y, x + bar_width, chart_y + chart_height], fill=color)

        # Draw value label
        draw.text((x + bar_width // 4, y - 20), f"{int(value * 100)}%", fill=0, font=small_font)

        # Draw x-axis label
        draw.text((x + bar_width // 4, chart_y + chart_height + 10), label, fill=0, font=small_font)

    return img


def main() -> None:
    """Run the 2bpp grayscale demo."""
    parser = argparse.ArgumentParser(description="2bpp grayscale demo")
    parser.add_argument("vcom", type=float, help="VCOM voltage (e.g., -2.0)")
    parser.add_argument(
        "--demo",
        choices=["palette", "icons", "chart", "all"],
        default="all",
        help="Demo mode to display",
    )
    args = parser.parse_args()

    # Enable debug logging to see performance metrics
    logging.basicConfig(level=logging.DEBUG)

    print(f"Initializing display with VCOM={args.vcom}V...")
    display = EPaperDisplay(vcom=args.vcom)

    try:
        width, height = display.init()
        print(f"Display initialized: {width}x{height}")

        if args.demo in {"palette", "all"}:
            print("\n=== Displaying 4-level grayscale palette ===")
            palette_img = create_grayscale_palette()

            # Center the palette
            x = (width - palette_img.width) // 2
            y = 50

            display.clear()
            display.display_image(
                palette_img, x=x, y=y, mode=DisplayMode.GC16, pixel_format=PixelFormat.BPP_2
            )

            if args.demo == "all":
                input("\nPress Enter to continue to icons demo...")

        if args.demo in {"icons", "all"}:
            print("\n=== Displaying icon grid with 2bpp ===")
            print("Simple graphics with 4 gray levels")

            icons_img = create_icon_grid(min(width, height) - 100)

            # Center the icons
            x = (width - icons_img.width) // 2
            y = (height - icons_img.height) // 2

            display.clear()
            display.display_image(
                icons_img, x=x, y=y, mode=DisplayMode.GC16, pixel_format=PixelFormat.BPP_2
            )

            if args.demo == "all":
                input("\nPress Enter to continue to chart demo...")

        if args.demo in {"chart", "all"}:
            print("\n=== Displaying chart with 2bpp ===")
            print("Charts and graphs work well with limited gray levels")

            chart_img = create_chart(width, height)
            display.display_image(chart_img, mode=DisplayMode.GC16, pixel_format=PixelFormat.BPP_2)

        print("\n=== 2bpp Mode Benefits ===")
        print("• 25% data size (1/4 of 8bpp)")
        print("• 4 distinct gray levels: 0, 85, 170, 255")
        print("• Good for UI elements and simple graphics")
        print("• Faster than 4bpp/8bpp, more versatile than 1bpp")

    finally:
        display.close()
        print("\nDisplay closed.")


if __name__ == "__main__":
    main()
