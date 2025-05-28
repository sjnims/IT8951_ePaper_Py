#!/usr/bin/env python3
"""Basic example of using the IT8951 e-paper display."""

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode


def main() -> None:
    """Run basic display example."""
    print("Initializing e-paper display...")

    display = EPaperDisplay(vcom=-2.0)

    try:
        width, height = display.init()
        print(f"Display initialized: {width}x{height} pixels")

        print("Clearing display to white...")
        display.clear(color=0xFF)

        print("Drawing test pattern...")
        img = Image.new("L", (400, 300))

        for y in range(300):
            for x in range(400):
                if (x // 50 + y // 50) % 2 == 0:
                    img.putpixel((x, y), 0)
                else:
                    img.putpixel((x, y), 255)

        print("Displaying checkerboard pattern...")
        # Use default 8bpp format
        display.display_image(img, x=100, y=100, mode=DisplayMode.GC16)

        # Or use 4bpp format for better performance (recommended by Waveshare)
        # display.display_image(img, x=100, y=100, mode=DisplayMode.GC16,
        #                      pixel_format=PixelFormat.BPP_4)

        print("Display complete!")

    finally:
        display.close()
        print("Display closed.")


if __name__ == "__main__":
    main()
