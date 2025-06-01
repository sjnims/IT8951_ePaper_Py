#!/usr/bin/env python3
"""Battery-powered device optimization demo.

This example demonstrates best practices for using the IT8951 e-paper display
in battery-powered applications, combining power management with performance
optimization techniques.

Key strategies demonstrated:
1. Aggressive power management with auto-sleep
2. Optimal bit depth selection (1bpp/2bpp for low power)
3. Partial updates to minimize power consumption
4. DU mode for fast, low-power updates
5. Power state monitoring
6. Batch operations to minimize wake time

Usage:
    python battery_powered_demo.py -v <VCOM_VALUE>

Example:
    python battery_powered_demo.py -v -2.36
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode, PixelFormat, PowerState
from IT8951_ePaper_Py.exceptions import IT8951Error


def create_clock_display(width: int, height: int) -> Image.Image:
    """Create a simple clock display for battery-powered device.

    Args:
        width: Display width
        height: Display height

    Returns:
        Clock display image
    """
    # Create 1-bit image for minimal power consumption
    img = Image.new("1", (width, height), 1)  # White background
    draw = ImageDraw.Draw(img)

    # Draw time in center
    current_time = datetime.now().strftime("%H:%M")

    # Try to use a simple font (fallback to default if not available)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
    except Exception:
        font = ImageFont.load_default()

    # Calculate text position
    bbox = draw.textbbox((0, 0), current_time, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # Draw text
    draw.text((x, y), current_time, fill=0, font=font)  # Black text

    # Add battery indicator
    battery_y = height - 100
    draw.text((50, battery_y), "Battery Mode: ON", fill=0, font=font)

    return img


def create_status_bar(width: int, status: str) -> Image.Image:
    """Create a minimal status bar for partial updates.

    Args:
        width: Display width
        status: Status message

    Returns:
        Status bar image
    """
    img = Image.new("1", (width, 50), 1)  # White background
    draw = ImageDraw.Draw(img)

    # Draw status text
    draw.text((10, 15), status, fill=0)

    return img


def battery_powered_clock_demo(display: EPaperDisplay) -> None:
    """Demonstrate battery-powered clock application.

    Uses minimal power by:
    - Using 1bpp for display
    - Partial updates for time changes
    - DU mode for fast updates
    - Auto-sleep between updates
    """
    width, height = display.init()
    print(f"Display initialized: {width}x{height}")

    # Clear display once with INIT mode
    print("\nClearing display...")
    display.clear()

    # Configure aggressive power management
    display.set_auto_sleep_timeout(5.0)  # Sleep after 5 seconds
    print("Auto-sleep configured: 5 seconds")

    # Initial clock display
    print("\nDrawing initial clock display...")
    clock_img = create_clock_display(width, height)
    display.display_image(
        clock_img,
        pixel_format=PixelFormat.BPP_1,  # 1bpp for lowest power
        mode=DisplayMode.GC16,  # Good quality for initial display
    )

    # Simulate battery-powered operation
    print("\nEntering battery-powered clock mode...")
    print("Press Ctrl+C to exit")

    last_minute = datetime.now().minute
    update_count = 0

    try:
        while True:
            # Check power state
            status = display.get_device_status()
            power_state = status["power_state"]

            # Only update when minute changes
            current_minute = datetime.now().minute
            if current_minute != last_minute:
                update_count += 1

                # Wake display if sleeping
                if power_state == PowerState.SLEEP:
                    print(f"\n[Update {update_count}] Waking display...")
                    display.wake()

                # Update time with minimal power usage
                print("Updating time (minute changed)...")
                clock_img = create_clock_display(width, height)

                # Use DU mode for fast, low-power update
                display.display_image(
                    clock_img,
                    pixel_format=PixelFormat.BPP_1,
                    mode=DisplayMode.DU,  # Fast 2-level update
                )

                last_minute = current_minute

                # Every 10 updates, do a full refresh to prevent ghosting
                if update_count % 10 == 0:
                    print("Performing full refresh to prevent ghosting...")
                    display.display_image(
                        clock_img, pixel_format=PixelFormat.BPP_1, mode=DisplayMode.GC16
                    )

            # Sleep to save battery (display will auto-sleep)
            time.sleep(10)  # Check every 10 seconds

    except KeyboardInterrupt:
        print("\nExiting battery-powered mode...")


def demonstrate_power_optimization(display: EPaperDisplay) -> None:
    """Demonstrate various power optimization techniques."""
    width, height = display.init()

    print("\n" + "=" * 60)
    print("BATTERY POWER OPTIMIZATION TECHNIQUES")
    print("=" * 60)

    # 1. Bit depth comparison for power consumption
    print("\n1. BIT DEPTH POWER COMPARISON")
    print("-" * 40)

    # Create test pattern
    test_img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(test_img)
    for i in range(0, width, 100):
        draw.line([(i, 0), (i, height)], fill=0, width=2)

    # Measure update time as proxy for power consumption
    formats = [
        (PixelFormat.BPP_1, "1bpp (lowest power)"),
        (PixelFormat.BPP_2, "2bpp (low power)"),
        (PixelFormat.BPP_4, "4bpp (moderate power)"),
        (PixelFormat.BPP_8, "8bpp (highest power)"),
    ]

    for pixel_format, description in formats:
        start_time = time.time()
        display.display_image(test_img, pixel_format=pixel_format, mode=DisplayMode.DU)
        update_time = time.time() - start_time
        print(f"{description}: {update_time:.3f}s")
        time.sleep(1)

    # 2. Display mode power comparison
    print("\n2. DISPLAY MODE POWER COMPARISON")
    print("-" * 40)

    modes = [
        (DisplayMode.DU, "DU (fastest, lowest power)"),
        (DisplayMode.A2, "A2 (fast, low power)"),
        (DisplayMode.GL16, "GL16 (moderate)"),
        (DisplayMode.GC16, "GC16 (slowest, highest power)"),
    ]

    for mode, description in modes:
        start_time = time.time()
        display.display_image(test_img, pixel_format=PixelFormat.BPP_1, mode=mode)
        update_time = time.time() - start_time
        print(f"{description}: {update_time:.3f}s")
        time.sleep(1)

    # 3. Partial update demonstration
    print("\n3. PARTIAL UPDATE POWER SAVING")
    print("-" * 40)

    # Full update baseline
    start_time = time.time()
    display.display_image(test_img)
    full_time = time.time() - start_time
    print(f"Full screen update: {full_time:.3f}s")

    # Partial update (10% of screen)
    partial_width = width // 10
    partial_height = height // 10
    partial_img = test_img.crop((0, 0, partial_width, partial_height))

    start_time = time.time()
    display.display_image(partial_img, x=0, y=0)
    partial_time = time.time() - start_time
    print(f"Partial update (10%): {partial_time:.3f}s")
    print(f"Power savings: {(1 - partial_time / full_time) * 100:.1f}%")

    # 4. Sleep mode demonstration
    print("\n4. SLEEP MODE POWER SAVING")
    print("-" * 40)

    print("Entering sleep mode...")
    display.sleep()
    status = display.get_device_status()
    print(f"Power state: {status['power_state']}")

    print("Sleeping for 3 seconds (simulating idle time)...")
    time.sleep(3)

    print("Waking up...")
    display.wake()
    status = display.get_device_status()
    print(f"Power state: {status['power_state']}")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Battery-powered device optimization demo")
    parser.add_argument(
        "-v", "--vcom", type=float, required=True, help="VCOM voltage value (e.g., -2.36)"
    )
    parser.add_argument("--clock", action="store_true", help="Run battery-powered clock demo")

    args = parser.parse_args()

    print("=" * 60)
    print("IT8951 E-Paper Battery-Powered Device Demo")
    print("=" * 60)
    print(f"\nVCOM: {args.vcom}V")
    print("\nThis demo shows power optimization techniques for")
    print("battery-powered e-paper applications.")

    try:
        # Use context manager for automatic power management
        with EPaperDisplay(vcom=args.vcom) as display:
            if args.clock:
                battery_powered_clock_demo(display)
            else:
                demonstrate_power_optimization(display)

                # Offer to run clock demo
                print("\n" + "=" * 60)
                response = input("Run battery-powered clock demo? (y/n): ")
                if response.lower() == "y":
                    battery_powered_clock_demo(display)

        print("\nDisplay automatically entered sleep mode on exit")
        print("Demo completed successfully!")

    except IT8951Error as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
