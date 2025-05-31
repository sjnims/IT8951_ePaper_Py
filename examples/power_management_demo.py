#!/usr/bin/env python3
"""Example demonstrating power management features of the IT8951 e-paper display.

This example shows how to:
1. Use standby and sleep modes to save power
2. Wake the display from power-saving modes
3. Check the current power state
4. Set up automatic sleep timeout
5. Use context manager for automatic power management
"""

import time

from PIL import Image, ImageDraw, ImageFont

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import PowerState


def create_test_image(width: int, height: int, text: str) -> Image.Image:
    """Create a test image with text."""
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
    except Exception:
        font = ImageFont.load_default()

    # Calculate text position for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    draw.text((x, y), text, fill=0, font=font)
    return img


def demo_standby_mode(display: EPaperDisplay, width: int, height: int) -> None:
    """Demonstrate standby mode functionality."""
    print("\n--- STANDBY MODE DEMO ---")
    print("Entering standby mode...")
    display.standby()
    print(f"Power state: {display.power_state.name}")
    print("In standby mode, the display retains its image but uses less power.")
    print("Waiting 3 seconds...")
    time.sleep(3)

    print("Waking from standby...")
    display.wake()
    print(f"Power state: {display.power_state.name}")

    # Update display after wake
    img = create_test_image(width, height, "WOKE FROM STANDBY")
    display.display_image(img)
    time.sleep(2)


def demo_sleep_mode(display: EPaperDisplay, width: int, height: int) -> None:
    """Demonstrate sleep mode functionality."""
    print("\n--- SLEEP MODE DEMO ---")
    print("Entering sleep mode...")
    display.sleep()
    print(f"Power state: {display.power_state.name}")
    print("In sleep mode, the display uses minimal power.")
    print("Waiting 3 seconds...")
    time.sleep(3)

    print("Waking from sleep...")
    display.wake()
    print(f"Power state: {display.power_state.name}")

    # Display needs refresh after sleep
    display.clear()
    img = create_test_image(width, height, "WOKE FROM SLEEP")
    display.display_image(img)
    time.sleep(2)


def demo_auto_sleep(display: EPaperDisplay, width: int, height: int) -> None:
    """Demonstrate auto-sleep timeout functionality."""
    print("\n--- AUTO-SLEEP TIMEOUT DEMO ---")
    print("Setting auto-sleep timeout to 5 seconds...")
    display.set_auto_sleep_timeout(5.0)

    print("Displaying image and waiting for auto-sleep...")
    img = create_test_image(width, height, "AUTO-SLEEP TEST")
    display.display_image(img)

    # Monitor power state
    for i in range(8):
        print(f"Time: {i}s, Power state: {display.power_state.name}")
        time.sleep(1)

        # Manually check for auto-sleep timeout
        display.check_auto_sleep()

    # Wake up if asleep
    if display.power_state != PowerState.ACTIVE:
        print("Waking display...")
        display.wake()
        display.clear()

    # Disable auto-sleep
    print("\nDisabling auto-sleep...")
    display.set_auto_sleep_timeout(None)


def demo_device_status(display: EPaperDisplay) -> None:
    """Demonstrate device status information."""
    print("\n--- DEVICE STATUS DEMO ---")
    print("Getting comprehensive device status...")

    # Get device status
    status = display.get_device_status()

    print("\nDevice Information:")
    print(f"  Panel Size: {status['panel_width']}x{status['panel_height']} pixels")
    print(f"  Memory Address: {status['memory_address']}")
    print(f"  Firmware Version: {status['fw_version']}")
    print(f"  LUT Version: {status['lut_version']}")

    print("\nRuntime Status:")
    print(f"  Power State: {status['power_state']}")
    print(f"  VCOM Voltage: {status['vcom_voltage']}V")
    print(f"  A2 Refresh Count: {status['a2_refresh_count']}/{status['a2_refresh_limit']}")
    print(
        f"  Auto-sleep Timeout: {status['auto_sleep_timeout']}s"
        if status["auto_sleep_timeout"]
        else "  Auto-sleep: Disabled"
    )
    print(f"  Enhanced Driving: {'Enabled' if status['enhanced_driving'] else 'Disabled'}")


def demo_context_manager() -> None:
    """Demonstrate context manager with auto-sleep."""
    print("\n--- CONTEXT MANAGER DEMO ---")
    print("Using context manager with auto-sleep...")

    # Demonstrate context manager with auto-sleep
    with EPaperDisplay(vcom=-1.45) as display:
        display.set_auto_sleep_timeout(10.0)  # Set 10 second timeout
        width, height = display.init()

        img = create_test_image(width, height, "CONTEXT MANAGER")
        display.display_image(img)
        print("Display will automatically sleep when context exits...")
        time.sleep(2)

    print("Context exited - display should be in sleep mode and closed.")


def main() -> None:
    """Main demo function."""
    print("IT8951 E-Paper Power Management Demo")
    print("===================================\n")

    # Initialize display with proper VCOM voltage
    print("Initializing display...")
    display = EPaperDisplay(vcom=-1.45)  # Adjust VCOM to match your display
    width, height = display.init()
    print(f"Display initialized: {width}x{height} pixels")
    print(f"Initial power state: {display.power_state.name}\n")

    # Display an initial image
    print("Displaying initial image...")
    img = create_test_image(width, height, "ACTIVE MODE")
    display.display_image(img)
    time.sleep(2)

    # Run demos
    demo_device_status(display)
    demo_standby_mode(display, width, height)
    demo_sleep_mode(display, width, height)
    demo_auto_sleep(display, width, height)

    # Cleanup
    display.close()

    # Context manager demo
    demo_context_manager()

    print("\nPower management demo complete!")


if __name__ == "__main__":
    main()
