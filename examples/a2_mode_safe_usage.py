#!/usr/bin/env python3
"""Example demonstrating safe A2 mode usage with auto-clear protection.

This example shows how the driver automatically protects against ghosting
by clearing the display after a certain number of A2 refreshes.
"""

import sys
import time

from PIL import Image, ImageDraw, ImageFont

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayConstants, DisplayMode


def create_text_image(text: str, width: int = 400, height: int = 200) -> Image.Image:
    """Create a simple text image for display.

    Args:
        text: Text to display.
        width: Image width.
        height: Image height.

    Returns:
        PIL Image with text.
    """
    img = Image.new("L", (width, height), DisplayConstants.GRAYSCALE_MAX)  # White background
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
    except OSError:
        font = ImageFont.load_default()

    # Center the text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    draw.text((x, y), text, fill=0, font=font)  # Black text
    return img


def main() -> None:  # noqa: PLR0915
    """Demonstrate safe A2 mode usage."""
    if len(sys.argv) < 2:
        print("Usage: python a2_mode_safe_usage.py <vcom_voltage>")
        print("Example: python a2_mode_safe_usage.py -1.45")
        print("\n⚠️  IMPORTANT: The VCOM voltage MUST match your display's specification!")
        print("   Check the FPC cable on your display for the correct VCOM value.")
        sys.exit(1)

    vcom = float(sys.argv[1])
    print("A2 Mode Safe Usage Demo")
    print("=======================")
    print()
    print("This demo shows automatic protection against A2 mode ghosting.")
    print("The display will auto-clear after 10 A2 refreshes (default).")
    print(f"Using VCOM voltage: {vcom}V")
    print()

    # Initialize display with default A2 limit (10)
    display = EPaperDisplay(vcom=vcom)
    width, height = display.init()
    print(f"Display size: {width}x{height}")
    print(f"A2 refresh limit: {display.a2_refresh_limit}")
    print()

    # Clear display first
    print("Clearing display...")
    display.clear()
    time.sleep(1)

    # Demonstrate A2 refreshes with auto-clear
    print("\nStarting A2 refresh demonstration...")
    print("Watch for the warning message and auto-clear!")
    print()

    for i in range(15):  # More than the limit to trigger auto-clear
        # Create an image with the refresh count
        img = create_text_image(f"A2 Refresh #{i + 1}")

        # Display using A2 mode
        print(f"A2 refresh {i + 1} (current count: {display.a2_refresh_count})")
        display.display_image(img, x=100, y=100, mode=DisplayMode.A2)

        # Small delay to see the update
        time.sleep(0.5)

        # Check if auto-clear happened
        if display.a2_refresh_count == 0 and i > 0:
            print("✓ Auto-clear triggered! Counter reset to 0")
            print()

    print("\nDemo complete!")
    print()

    # Demonstrate custom limit
    print("Creating display with custom A2 limit of 5...")
    display2 = EPaperDisplay(vcom=vcom, a2_refresh_limit=5)
    display2.init()
    display2.clear()

    print("Performing 6 A2 refreshes with limit of 5...")
    for i in range(6):
        img = create_text_image(f"Custom #{i + 1}")
        print(f"  Refresh {i + 1} (count: {display2.a2_refresh_count})")
        display2.display_image(img, x=100, y=300, mode=DisplayMode.A2)
        time.sleep(0.5)

    print()
    print("Demonstration complete!")
    print()
    print("Key points:")
    print("- A2 mode provides fast updates but can cause ghosting")
    print("- Auto-clear prevents ghosting by using INIT mode periodically")
    print("- Default limit is 10, but can be customized")
    print("- Set a2_refresh_limit=0 to disable auto-clearing")

    # Clean up
    display.close()
    display2.close()


if __name__ == "__main__":
    main()
