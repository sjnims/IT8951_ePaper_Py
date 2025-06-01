#!/usr/bin/env python3
"""Demo of extended display modes: GLR16, GLD16, and DU4.

This example demonstrates the three extended display modes that are
now implemented in the IT8951 driver for v0.7.0.

Note: Hardware support for these modes varies. They may not work on all
e-paper displays. Monitor your display behavior when testing.
"""

import time

from PIL import Image, ImageDraw, ImageFont

from IT8951_ePaper_Py import EPaperDisplay, constants


def create_ghosting_test_pattern(width: int, height: int) -> Image.Image:
    """Create a pattern specifically designed to test ghosting reduction."""
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    # Create alternating black and white stripes (common ghosting pattern)
    stripe_width = 50
    for i in range(0, width, stripe_width * 2):
        draw.rectangle((i, 0, i + stripe_width, height // 3), fill=0)

    # Add a checkerboard pattern (another ghosting-prone pattern)
    checker_size = 30
    y_start = height // 3
    y_end = 2 * height // 3
    for y in range(y_start, y_end, checker_size):
        for x in range(0, width, checker_size):
            if (x // checker_size + y // checker_size) % 2 == 0:
                draw.rectangle((x, y, x + checker_size, y + checker_size), fill=0)

    # Add gradient area to test grayscale levels
    gradient_start = 2 * height // 3
    for x in range(width):
        gray_value = int(x * 255 / width)
        draw.line((x, gradient_start, x, height), fill=gray_value)

    return img


def create_du4_test_pattern(width: int, height: int) -> Image.Image:
    """Create a pattern to test DU4 mode's 4 grayscale levels."""
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    # Create 4 distinct gray levels
    gray_levels = [0, 85, 170, 255]  # Black, dark gray, light gray, white
    section_width = width // 4
    num_sections = len(gray_levels)

    for i, gray in enumerate(gray_levels):
        x_start = i * section_width
        x_end = (i + 1) * section_width if i < num_sections - 1 else width
        draw.rectangle((x_start, 0, x_end, height // 2), fill=gray)

    # Add text labels
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except OSError:
        font = None

    y_text = height // 2 + 50
    labels = ["0", "85", "170", "255"]
    dark_sections = 2  # First two sections are dark
    for i, label in enumerate(labels):
        x_text = i * section_width + section_width // 2 - 20
        # White text on dark backgrounds, black on light
        text_color = 255 if i < dark_sections else 0
        draw.text((x_text, y_text), label, fill=text_color, font=font)

    return img


def test_glr16_mode(display: EPaperDisplay) -> None:
    """Test GLR16 (Ghost Reduction) mode."""
    print("\n" + "=" * 60)
    print("Testing GLR16 (Ghost Reduction) Mode")
    print("=" * 60)
    print("This mode reduces ghosting artifacts at the cost of speed.")
    print("Watch for cleaner transitions between black and white areas.")

    # First, create ghosting with standard mode
    print("\n1. Creating ghosting with GL16 mode...")
    pattern = create_ghosting_test_pattern(display.width, display.height)
    display.display_image(pattern, mode=constants.DisplayMode.GL16)
    time.sleep(2)

    # Clear to white
    print("2. Clearing to white (you may see ghosting)...")
    white = Image.new("L", (display.width, display.height), 255)
    display.display_image(white, mode=constants.DisplayMode.GL16)
    time.sleep(2)

    # Now use GLR16 to reduce ghosting
    print("3. Using GLR16 mode to display pattern with ghost reduction...")
    display.display_image(pattern, mode=constants.DisplayMode.GLR16)
    time.sleep(2)

    print("4. Clearing with GLR16 (should have less ghosting)...")
    display.display_image(white, mode=constants.DisplayMode.GLR16)

    print("\nGLR16 test complete. Did you notice reduced ghosting?")
    input("Press Enter to continue...")


def test_gld16_mode(display: EPaperDisplay) -> None:
    """Test GLD16 (Ghost Level Detection) mode."""
    print("\n" + "=" * 60)
    print("Testing GLD16 (Ghost Level Detection) Mode")
    print("=" * 60)
    print("This mode analyzes the display to adaptively compensate for ghosting.")
    print("It may take longer but should provide optimal ghost reduction.")

    # Create a complex pattern
    print("\n1. Displaying complex pattern with GLD16...")

    img = Image.new("L", (display.width, display.height), 255)
    draw = ImageDraw.Draw(img)

    # Mix of patterns that typically cause ghosting
    # Solid black rectangle
    draw.rectangle((50, 50, 250, 250), fill=0)
    # Fine lines
    for i in range(300, 500, 5):
        draw.line((i, 50, i, 250), fill=0 if i % 10 == 0 else 128)
    # Text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
        draw.text((100, 300), "GLD16 TEST", fill=0, font=font)
    except OSError:
        draw.text((100, 300), "GLD16 TEST", fill=0)

    display.display_image(img, mode=constants.DisplayMode.GLD16)
    time.sleep(3)

    print("2. Clearing with GLD16 (adaptive ghost compensation)...")
    white = Image.new("L", (display.width, display.height), 255)
    display.display_image(white, mode=constants.DisplayMode.GLD16)

    print("\nGLD16 test complete. The mode should have analyzed and compensated for ghosting.")
    input("Press Enter to continue...")


def test_du4_mode(display: EPaperDisplay) -> None:
    """Test DU4 (Direct Update 4-level) mode."""
    print("\n" + "=" * 60)
    print("Testing DU4 (Direct Update 4-level) Mode")
    print("=" * 60)
    print("This mode provides fast updates with 4 grayscale levels.")
    print("Faster than GC16/GL16 but with limited gray levels.")

    # Test pattern with 4 gray levels
    print("\n1. Displaying 4-level grayscale pattern...")
    pattern = create_du4_test_pattern(display.width, display.height)

    start_time = time.time()
    display.display_image(
        pattern, mode=constants.DisplayMode.DU4, pixel_format=constants.PixelFormat.BPP_2
    )
    du4_time = time.time() - start_time
    print(f"   DU4 update time: {du4_time:.3f}s")

    time.sleep(2)

    # Compare with GL16
    print("\n2. Comparing with GL16 mode (16 levels)...")
    start_time = time.time()
    display.display_image(pattern, mode=constants.DisplayMode.GL16)
    gl16_time = time.time() - start_time
    print(f"   GL16 update time: {gl16_time:.3f}s")

    print(f"\nDU4 was {gl16_time / du4_time:.1f}x faster than GL16")
    print("DU4 should show only 4 distinct gray levels vs GL16's smooth gradient.")
    input("Press Enter to continue...")


def compare_all_modes(display: EPaperDisplay) -> None:
    """Compare all display modes with the same image."""
    print("\n" + "=" * 60)
    print("Comparing All Display Modes")
    print("=" * 60)

    # Create a test image with various elements
    img = Image.new("L", (display.width, display.height), 255)
    draw = ImageDraw.Draw(img)

    # Title
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except OSError:
        title_font = text_font = None

    draw.text((50, 20), "Display Mode Comparison", fill=0, font=title_font)

    # Gradient bar
    gradient_y = 100
    gradient_height = 60
    for x in range(100, display.width - 100):
        gray = int((x - 100) * 255 / (display.width - 200))
        draw.line((x, gradient_y, x, gradient_y + gradient_height), fill=gray)

    # Text samples
    text_y = 200
    draw.text((50, text_y), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", fill=0, font=text_font)
    draw.text((50, text_y + 40), "abcdefghijklmnopqrstuvwxyz", fill=64, font=text_font)
    draw.text((50, text_y + 80), "0123456789 !@#$%^&*()", fill=128, font=text_font)

    # Geometric shapes
    shapes_y = 350
    # Black square
    draw.rectangle((50, shapes_y, 150, shapes_y + 100), fill=0)
    # Gray square
    draw.rectangle((200, shapes_y, 300, shapes_y + 100), fill=128)
    # Outlined square
    draw.rectangle((350, shapes_y, 450, shapes_y + 100), outline=0, width=3)

    # Test each mode
    modes_to_test = [
        (constants.DisplayMode.INIT, "INIT", None),
        (constants.DisplayMode.DU, "DU", constants.PixelFormat.BPP_1),
        (constants.DisplayMode.A2, "A2", constants.PixelFormat.BPP_1),
        (constants.DisplayMode.DU4, "DU4", constants.PixelFormat.BPP_2),
        (constants.DisplayMode.GL16, "GL16", constants.PixelFormat.BPP_4),
        (constants.DisplayMode.GC16, "GC16", constants.PixelFormat.BPP_4),
        (constants.DisplayMode.GLR16, "GLR16", constants.PixelFormat.BPP_4),
        (constants.DisplayMode.GLD16, "GLD16", constants.PixelFormat.BPP_4),
    ]

    print("\nTesting each mode with the same image...")
    print("Mode    | Time    | Quality | Notes")
    print("--------|---------|---------|------------------------")

    for mode, name, pixel_format in modes_to_test:
        try:
            # Add mode name to image
            mode_img = img.copy()
            mode_draw = ImageDraw.Draw(mode_img)
            mode_draw.rectangle((display.width - 250, 20, display.width - 50, 80), fill=255)
            mode_draw.text((display.width - 230, 30), f"Mode: {name}", fill=0, font=title_font)

            # Display with timing
            start_time = time.time()
            if pixel_format:
                display.display_image(mode_img, mode=mode, pixel_format=pixel_format)
            else:
                display.display_image(mode_img, mode=mode)
            update_time = time.time() - start_time

            # Get mode characteristics
            mode_info = constants.DisplayModeCharacteristics.MODE_INFO.get(mode, {})
            quality = mode_info.get("quality", "?")
            notes = mode_info.get("use_case", "")

            print(f"{name:7} | {update_time:6.3f}s | {quality:7} | {notes}")

            time.sleep(1)  # Brief pause to observe

        except Exception as e:
            print(f"{name:7} | ERROR   | N/A     | {e!s}")


def main() -> None:
    """Main demo function."""
    print("IT8951 Extended Display Modes Demo")
    print("=" * 60)
    print("\nThis demo tests the extended display modes introduced in v0.7.0:")
    print("- GLR16: Ghost Reduction 16-level")
    print("- GLD16: Ghost Level Detection 16-level")
    print("- DU4: Direct Update 4-level")
    print("\nNote: These modes may not work on all hardware.")

    # Initialize display
    print("\nInitializing display...")
    try:
        with EPaperDisplay(vcom=-2.0) as display:
            print(f"Display initialized: {display.width}x{display.height}")

            # Clear display first
            print("\nClearing display...")
            display.clear()
            time.sleep(1)

            # Run tests
            while True:
                print("\n" + "=" * 60)
                print("Select a test:")
                print("1. Test GLR16 (Ghost Reduction)")
                print("2. Test GLD16 (Ghost Level Detection)")
                print("3. Test DU4 (4-Level Fast Update)")
                print("4. Compare all modes")
                print("5. Exit")
                print("=" * 60)

                choice = input("Enter choice (1-5): ").strip()

                if choice == "1":
                    test_glr16_mode(display)
                elif choice == "2":
                    test_gld16_mode(display)
                elif choice == "3":
                    test_du4_mode(display)
                elif choice == "4":
                    compare_all_modes(display)
                elif choice == "5":
                    break
                else:
                    print("Invalid choice. Please try again.")

            print("\nDemo complete!")

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
