#!/usr/bin/env python3
"""VCOM calibration tool for IT8951 e-paper display."""
# ruff: noqa: PLR2004

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayConstants, DisplayMode


def create_test_pattern(width: int, height: int) -> Image.Image:
    """Create a test pattern for VCOM calibration."""
    img = Image.new("L", (width, height), color=DisplayConstants.GRAYSCALE_MAX)
    draw = ImageDraw.Draw(img)

    for i in range(0, 256, 16):
        x = (i // 16) * (width // 16)
        gray_value = i
        draw.rectangle([x, 0, x + width // 16, height], fill=gray_value)

    draw.line([(0, height // 2), (width, height // 2)], fill=0, width=2)
    draw.line([(width // 2, 0), (width // 2, height)], fill=0, width=2)

    return img


def main() -> None:  # noqa: PLR0912, PLR0915
    """Run VCOM calibration."""
    print("IT8951 VCOM Calibration Tool")
    print("============================")
    print()
    print("This tool helps you find the optimal VCOM voltage for your display.")
    print("The VCOM voltage affects image quality and ghosting.")
    print()

    # Default VCOM value - check your display's FPC cable
    current_vcom = -2.0

    if len(sys.argv) > 1:
        try:
            current_vcom = float(sys.argv[1])
        except ValueError:
            print(f"Invalid VCOM value: {sys.argv[1]}")
            sys.exit(1)
    else:
        print("Usage: python vcom_calibration.py [initial_vcom]")
        print("Example: python vcom_calibration.py -1.45")
        print(f"\nStarting with default VCOM: {current_vcom}V")
        print("(Check your display's FPC cable for the recommended starting value)\n")

    display = EPaperDisplay(vcom=current_vcom)

    try:
        width, height = display.init()
        print(f"Display initialized: {width}x{height} pixels")

        current_vcom = display.get_vcom()
        print(f"Current VCOM: {current_vcom:.2f}V")
        print()

        test_pattern = create_test_pattern(width, height)

        while True:
            print(f"\nCurrent VCOM: {current_vcom:.2f}V")
            print("Commands:")
            print("  + : Increase VCOM by 0.1V")
            print("  - : Decrease VCOM by 0.1V")
            print("  f : Fine adjust (+0.01V)")
            print("  F : Fine adjust (-0.01V)")
            print("  r : Refresh display")
            print("  s : Save and exit")
            print("  q : Quit without saving")

            cmd = input("\nEnter command: ").strip().lower()

            if cmd == "q":
                print("Exiting without saving.")
                break
            if cmd == "s":
                print(f"Optimal VCOM voltage: {current_vcom:.2f}V")
                print("Add this to your code:")
                print(f"  display = EPaperDisplay(vcom={current_vcom:.2f})")
                break
            if cmd == "+":
                new_vcom = current_vcom + 0.1
                if new_vcom > DisplayConstants.MAX_VCOM:
                    print(f"VCOM cannot exceed {DisplayConstants.MAX_VCOM}V")
                    continue
                current_vcom = new_vcom
            elif cmd == "-":
                new_vcom = current_vcom - 0.1
                if new_vcom < DisplayConstants.MIN_VCOM:
                    print(f"VCOM cannot go below {DisplayConstants.MIN_VCOM}V")
                    continue
                current_vcom = new_vcom
            elif cmd == "f":
                new_vcom = current_vcom + 0.01
                if new_vcom > DisplayConstants.MAX_VCOM:
                    print(f"VCOM cannot exceed {DisplayConstants.MAX_VCOM}V")
                    continue
                current_vcom = new_vcom
            elif cmd == "F":
                new_vcom = current_vcom - 0.01
                if new_vcom < DisplayConstants.MIN_VCOM:
                    print(f"VCOM cannot go below {DisplayConstants.MIN_VCOM}V")
                    continue
                current_vcom = new_vcom
            elif cmd == "r":
                pass
            else:
                print("Invalid command")
                continue

            print(f"Setting VCOM to {current_vcom:.2f}V...")
            display.set_vcom(current_vcom)

            print("Displaying test pattern...")
            display.clear()
            display.display_image(test_pattern, x=0, y=0, mode=DisplayMode.GC16)

            print("Look for:")
            print("- Clear grayscale transitions")
            print("- No ghosting or artifacts")
            print("- Good contrast")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        display.close()
        print("Display closed.")


if __name__ == "__main__":
    main()
