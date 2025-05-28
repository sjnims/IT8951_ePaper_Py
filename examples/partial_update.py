#!/usr/bin/env python3
"""Example of partial display updates for IT8951 e-paper."""

import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode


def create_clock_image(width: int, height: int, time_str: str) -> Image.Image:
    """Create an image with current time."""
    img = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
    except OSError:
        font = ImageFont.load_default()

    text_bbox = draw.textbbox((0, 0), time_str, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    x = (width - text_width) // 2
    y = (height - text_height) // 2

    draw.text((x, y), time_str, fill=0, font=font)

    return img


def main() -> None:
    """Demonstrate partial display updates."""
    print("Initializing e-paper display...")

    display = EPaperDisplay(vcom=-2.0)

    try:
        width, height = display.init()
        print(f"Display initialized: {width}x{height} pixels")

        print("Clearing display...")
        display.clear()

        clock_width = 400
        clock_height = 100
        clock_x = (width - clock_width) // 2
        clock_y = 50

        print("Starting clock display (press Ctrl+C to stop)...")
        print(f"Clock position: ({clock_x}, {clock_y})")
        print(f"Clock size: {clock_width}x{clock_height}")

        try:
            while True:
                current_time = time.strftime("%H:%M:%S")

                clock_img = create_clock_image(clock_width, clock_height, current_time)

                display.display_partial(clock_img, x=clock_x, y=clock_y, mode=DisplayMode.DU)

                time.sleep(1)

        except KeyboardInterrupt:
            print("\nStopped by user")

        print("\nDrawing some shapes with partial updates...")

        for i in range(5):
            x = 100 + i * 150
            y = 300
            size = 100

            shape_img = np.zeros((size, size), dtype=np.uint8)

            if i % 2 == 0:
                shape_img[:] = 255
                shape_img[10:90, 10:90] = 0
            else:
                for row in range(size):
                    for col in range(size):
                        if (row - 50) ** 2 + (col - 50) ** 2 < 40**2:
                            shape_img[row, col] = 0
                        else:
                            shape_img[row, col] = 255

            display.display_partial(shape_img, x=x, y=y, mode=DisplayMode.A2)
            time.sleep(0.5)

        print("Partial update demo complete!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        display.close()
        print("Display closed.")


if __name__ == "__main__":
    main()
