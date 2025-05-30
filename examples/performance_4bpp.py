#!/usr/bin/env python3
"""Example demonstrating 4bpp performance improvements.

This example shows how to use 4bpp mode for faster display updates
while maintaining 16 grayscale levels, as recommended by Waveshare.
"""

import sys
import time

from PIL import Image

from IT8951_ePaper_Py.constants import DisplayConstants, DisplayMode, PixelFormat
from IT8951_ePaper_Py.display import EPaperDisplay


def measure_display_time(
    display: EPaperDisplay,
    image: Image.Image,
    pixel_format: PixelFormat,
    mode: DisplayMode = DisplayMode.GC16,
) -> float:
    """Measure time to display an image with given pixel format."""
    start_time = time.time()
    display.display_image(image, pixel_format=pixel_format, mode=mode)
    return time.time() - start_time


def main() -> None:
    """Run 4bpp performance demonstration."""
    if len(sys.argv) < 2:
        print("Usage: python performance_4bpp.py <vcom_voltage>")
        print("Example: python performance_4bpp.py -1.45")
        print("\n⚠️  IMPORTANT: The VCOM voltage MUST match your display's specification!")
        print("   Check the FPC cable on your display for the correct VCOM value.")
        sys.exit(1)

    vcom = float(sys.argv[1])
    print(f"Initializing e-paper display with VCOM: {vcom}V...")

    display = EPaperDisplay(vcom=vcom)

    try:
        # Get display dimensions
        width, height = display.init()
        print(f"\nDisplay: {width}x{height}")

        # Create or load a test image
        print("\nCreating test image...")
        # Create a gradient test pattern
        img_width, img_height = 800, 600
        image = Image.new("L", (img_width, img_height))

        # Create horizontal gradient
        for y in range(img_height):
            for x in range(img_width):
                # Create 16 distinct gray levels
                gray_level = int((x / img_width) * 16) * 16
                image.putpixel((x, y), min(gray_level, DisplayConstants.GRAYSCALE_MAX))

        # Clear display first
        print("\nClearing display...")
        display.clear()

        # Test 8bpp (standard) mode
        print("\nTesting 8bpp mode (standard)...")
        time_8bpp = measure_display_time(display, image, PixelFormat.BPP_8)
        print(f"8bpp display time: {time_8bpp:.2f} seconds")

        time.sleep(2)  # Pause between tests

        # Test 4bpp (recommended) mode
        print("\nTesting 4bpp mode (Waveshare recommended)...")
        time_4bpp = measure_display_time(display, image, PixelFormat.BPP_4)
        print(f"4bpp display time: {time_4bpp:.2f} seconds")

        # Calculate improvement
        data_reduction = 50  # 4bpp uses 50% less data than 8bpp
        time_improvement = ((time_8bpp - time_4bpp) / time_8bpp) * 100

        print("\nPerformance Summary:")
        print(f"- Data transmission reduced by {data_reduction}%")
        print(f"- Display time improved by {time_improvement:.1f}%")
        print("- Image quality: 16 grayscale levels maintained")

        # Test with different display modes
        print("\n\nTesting 4bpp with different display modes:")

        modes = [
            (DisplayMode.DU, "DU (Direct Update)"),
            (DisplayMode.GL16, "GL16 (16 Gray Levels)"),
            (DisplayMode.A2, "A2 (Fast 2-level)"),
        ]

        for mode, mode_name in modes:
            print(f"\n{mode_name}:")
            mode_time = measure_display_time(display, image, PixelFormat.BPP_4, mode)
            print(f"  Time: {mode_time:.2f} seconds")
            time.sleep(1)

        # Final clear
        print("\nClearing display...")
        display.clear()

    finally:
        display.close()
        print("\nDisplay closed.")


if __name__ == "__main__":
    main()
