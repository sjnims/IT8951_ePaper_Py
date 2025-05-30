#!/usr/bin/env python3
"""Basic example of using the IT8951 e-paper display."""

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayConstants, DisplayMode


def main() -> None:
    """Run basic display example."""
    if len(sys.argv) < 2:
        print("Usage: python basic_display.py <vcom_voltage>")
        print("Example: python basic_display.py -1.45")
        print("\n⚠️  IMPORTANT: The VCOM voltage MUST match your display's specification!")
        print("   Check the FPC cable on your display for the correct VCOM value.")
        print("   Using the wrong VCOM can result in poor image quality or display damage.")
        sys.exit(1)

    vcom = float(sys.argv[1])
    print(f"Initializing e-paper display with VCOM: {vcom}V...")

    display = EPaperDisplay(vcom=vcom)

    try:
        width, height = display.init()
        print(f"Display initialized: {width}x{height} pixels")

        print("Clearing display to white...")
        display.clear(color=DisplayConstants.DEFAULT_CLEAR_COLOR)

        print("Drawing test pattern...")
        img = Image.new("L", (400, 300))

        for y in range(300):
            for x in range(400):
                if (x // 50 + y // 50) % 2 == 0:
                    img.putpixel((x, y), 0)
                else:
                    img.putpixel((x, y), DisplayConstants.GRAYSCALE_MAX)

        print("Displaying checkerboard pattern...")
        # Uses default 4bpp format (recommended by Waveshare)
        display.display_image(img, x=100, y=100, mode=DisplayMode.GC16)

        # Or explicitly specify 8bpp format for full grayscale range
        # from IT8951_ePaper_Py.constants import PixelFormat
        # display.display_image(img, x=100, y=100, mode=DisplayMode.GC16,
        #                      pixel_format=PixelFormat.BPP_8)

        print("Display complete!")

    finally:
        display.close()
        print("Display closed.")


if __name__ == "__main__":
    main()
