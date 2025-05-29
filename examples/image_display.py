#!/usr/bin/env python3
"""Example of displaying images on IT8951 e-paper display."""

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayConstants, DisplayMode, Rotation


def main() -> None:
    """Display various images on e-paper."""
    if len(sys.argv) < 2:
        print("Usage: python image_display.py <image_path> [vcom_voltage]")
        print("Example: python image_display.py test.jpg -2.0")
        sys.exit(1)

    image_path = Path(sys.argv[1])
    vcom = float(sys.argv[2]) if len(sys.argv) > 2 else DisplayConstants.DEFAULT_VCOM

    if not image_path.exists():
        print(f"Error: Image file '{image_path}' not found")
        sys.exit(1)

    print(f"Loading image: {image_path}")
    print(f"Using VCOM voltage: {vcom}V")

    display = EPaperDisplay(vcom=vcom)

    try:
        width, height = display.init()
        print(f"Display initialized: {width}x{height} pixels")

        print("Clearing display...")
        display.clear()

        img = Image.open(image_path)
        print(f"Original image size: {img.size}")

        if img.width > width or img.height > height:
            print("Resizing image to fit display...")
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            print(f"Resized to: {img.size}")

        x = (width - img.width) // 2
        y = (height - img.height) // 2

        print(f"Displaying image at position ({x}, {y})...")
        display.display_image(img, x=x, y=y, mode=DisplayMode.GC16)

        print("Image displayed successfully!")

        input("Press Enter to display rotated version...")

        print("Displaying 90-degree rotated image...")
        display.display_image(img, x=100, y=100, mode=DisplayMode.GC16, rotation=Rotation.ROTATE_90)

        print("Done!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        display.close()
        print("Display closed.")


if __name__ == "__main__":
    main()
