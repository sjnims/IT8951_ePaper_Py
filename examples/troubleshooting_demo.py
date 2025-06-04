#!/usr/bin/env python3
"""Troubleshooting and diagnostics demo.

This example demonstrates how to diagnose and troubleshoot common issues
with the IT8951 e-paper display, including:

1. Communication problems
2. Display quality issues
3. Performance problems
4. Memory errors
5. Power management issues

The demo includes diagnostic tools and recovery strategies for each issue.

Usage:
    python troubleshooting_demo.py -v <VCOM_VALUE>

Example:
    python troubleshooting_demo.py -v -2.36
"""

import argparse
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode, PixelFormat, PowerState
from IT8951_ePaper_Py.exceptions import (
    CommunicationError,
    IT8951Error,
    IT8951MemoryError,
    IT8951TimeoutError,
)


def diagnose_communication(display: EPaperDisplay) -> None:
    """Diagnose communication issues."""
    print("\n1. DIAGNOSING COMMUNICATION")
    print("-" * 40)

    try:
        # Test basic communication
        print("Testing SPI communication...")
        status = display.get_device_status()
        print("✓ SPI communication OK")
        print(f"  Power state: {status['power_state']}")
        print(f"  Display size: {status['panel_width']}x{status['panel_height']}")

        # Test register access
        print("\nTesting register access...")
        vcom = display.get_vcom()
        print(f"✓ Register read OK (VCOM: {vcom}V)")

        # Test display update
        print("\nTesting display update...")
        # Small test pattern
        test_img = Image.new("L", (100, 100), 255)
        display.display_image(test_img, x=0, y=0)
        print("✓ Display update OK")

    except IT8951TimeoutError as e:
        print(f"✗ Timeout error: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check SPI connections (MOSI, MISO, SCK, CS)")
        print("2. Verify GPIO connections (RST, BUSY)")
        print("3. Ensure proper power supply (5V, sufficient current)")
        print("4. Try reducing SPI speed in constants.py")

    except CommunicationError as e:
        print(f"✗ Communication error: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check all cable connections")
        print("2. Verify Raspberry Pi SPI is enabled")
        print("3. Try power cycling the display")


def diagnose_display_quality(display: EPaperDisplay) -> None:
    """Diagnose display quality issues."""
    print("\n2. DIAGNOSING DISPLAY QUALITY")
    print("-" * 40)

    width, height = display.width, display.height

    # Create test patterns
    test_patterns: list[tuple[str, Image.Image]] = []

    # Pattern 1: Checkerboard for ghosting detection
    checker = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(checker)
    square_size = 50
    for y in range(0, height, square_size):
        for x in range(0, width, square_size):
            if (x // square_size + y // square_size) % 2 == 0:
                draw.rectangle([x, y, x + square_size, y + square_size], fill=0)
    test_patterns.append(("Checkerboard (ghosting test)", checker))

    # Pattern 2: Gradient for bit depth verification
    gradient = Image.new("L", (width, height))
    pixels = gradient.load()  # type: ignore
    if pixels is not None:
        for x in range(width):
            gray_value = int(255 * x / width)
            for y in range(height):
                pixels[x, y] = gray_value  # type: ignore
    test_patterns.append(("Gradient (bit depth test)", gradient))

    # Pattern 3: Fine lines for blur detection
    lines = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(lines)
    for i in range(0, width, 10):
        draw.line([(i, 0), (i, height)], fill=0, width=1)
    for i in range(0, height, 10):
        draw.line([(0, i), (width, i)], fill=0, width=1)
    test_patterns.append(("Fine lines (blur test)", lines))

    # Run tests
    for name, pattern in test_patterns:
        print(f"\nDisplaying {name}...")
        display.display_image(pattern, mode=DisplayMode.GC16)
        time.sleep(2)

        response = input("Any issues? (ghosting/blur/banding/none): ").lower()

        if "ghost" in response:
            print("\nGhosting detected. Solutions:")
            print("1. Use INIT mode to clear: display.clear()")
            print("2. Check VCOM voltage matches your display")
            print("3. Use A2 mode sparingly with auto-clear")
            display.clear()  # Clear ghosting

        elif "blur" in response:
            print("\nBlur detected. Solutions:")
            print("1. Enable enhanced driving for long cables")
            print("2. Check cable connections")
            print("3. Reduce SPI cable length if possible")
            print("Consider using enhanced driving in display initialization:")

        elif "band" in response:
            print("\nBanding detected. Solutions:")
            print("1. Check power supply stability")
            print("2. Verify proper grounding")
            print("3. Try different display modes")


def diagnose_performance(display: EPaperDisplay) -> None:
    """Diagnose performance issues."""
    print("\n3. DIAGNOSING PERFORMANCE")
    print("-" * 40)

    width, height = display.width, display.height
    test_img = Image.new("L", (width, height), 128)

    # Test different configurations
    configs = [
        ("8bpp + GC16", PixelFormat.BPP_8, DisplayMode.GC16),
        ("4bpp + GC16", PixelFormat.BPP_4, DisplayMode.GC16),
        ("1bpp + A2", PixelFormat.BPP_1, DisplayMode.A2),
        ("1bpp + DU", PixelFormat.BPP_1, DisplayMode.DU),
    ]

    print("\nPerformance test results:")
    print("-" * 40)

    for name, pixel_format, mode in configs:
        try:
            start = time.time()
            display.display_image(test_img, pixel_format=pixel_format, mode=mode)
            elapsed = time.time() - start
            print(f"{name:15} : {elapsed:.3f}s")
        except Exception as e:
            print(f"{name:15} : Failed - {e}")

    print("\nPerformance optimization tips:")
    print("1. Use lower bit depths (1bpp, 2bpp) for faster updates")
    print("2. Use DU/A2 modes for dynamic content")
    print("3. Use partial updates for small changes")
    print("4. Consider 4bpp as balance of quality/speed")


def diagnose_memory(display: EPaperDisplay) -> None:
    """Diagnose memory issues."""
    print("\n4. DIAGNOSING MEMORY ISSUES")
    print("-" * 40)

    width, height = display.width, display.height

    # Test memory limits
    print("Testing memory allocation...")

    # Calculate memory usage
    formats = [
        (PixelFormat.BPP_8, 1, "8bpp"),
        (PixelFormat.BPP_4, 2, "4bpp"),
        (PixelFormat.BPP_2, 4, "2bpp"),
        (PixelFormat.BPP_1, 8, "1bpp"),
    ]

    for pixel_format, pixels_per_byte, name in formats:
        memory_usage = (width * height) // pixels_per_byte
        print(
            f"\n{name} memory usage: {memory_usage:,} bytes ({memory_usage / 1024 / 1024:.2f} MB)"
        )

        # Try to allocate
        try:
            test_img = Image.new("L", (width, height), 128)
            display.display_image(test_img, pixel_format=pixel_format)
            print(f"✓ {name} allocation successful")
        except IT8951MemoryError as e:
            print(f"✗ {name} allocation failed: {e}")
            print("  Solutions:")
            print("  1. Use lower bit depth")
            print("  2. Use progressive loading for large images")
            print("  3. Reduce image size")


def diagnose_power_management(display: EPaperDisplay) -> None:
    """Diagnose power management issues."""
    print("\n5. DIAGNOSING POWER MANAGEMENT")
    print("-" * 40)

    # Test power states
    print("Testing power state transitions...")

    try:
        # Test current state
        status = display.get_device_status()
        print(f"Current state: {status['power_state']}")

        # Test sleep
        print("\nEntering sleep mode...")
        display.sleep()
        status = display.get_device_status()
        if status["power_state"] == PowerState.SLEEP:
            print("✓ Sleep mode OK")
        else:
            print("✗ Sleep mode failed")

        # Test wake
        print("\nWaking up...")
        display.wake()
        status = display.get_device_status()
        if status["power_state"] == PowerState.ACTIVE:
            print("✓ Wake OK")
        else:
            print("✗ Wake failed")

        # Test auto-sleep
        print("\nTesting auto-sleep (5 second timeout)...")
        display.set_auto_sleep_timeout(5.0)
        print("Waiting 6 seconds...")
        time.sleep(6)
        status = display.get_device_status()
        if status["power_state"] == PowerState.SLEEP:
            print("✓ Auto-sleep OK")
        else:
            print("✗ Auto-sleep failed")

    except Exception as e:
        print(f"✗ Power management error: {e}")
        print("\nTroubleshooting:")
        print("1. Check power supply stability")
        print("2. Verify controller firmware supports power management")
        print("3. Try manual sleep/wake commands")


def check_vcom_mismatch(display: EPaperDisplay, specified_vcom: float) -> None:
    """Check for VCOM mismatch issues."""
    print("\n6. CHECKING VCOM CONFIGURATION")
    print("-" * 40)

    try:
        # Read actual VCOM from device
        actual_vcom = display.get_vcom()
        print(f"Specified VCOM: {specified_vcom}V")
        print(f"Device VCOM: {actual_vcom}V")

        # Check for mismatch
        if abs(actual_vcom - specified_vcom) > 0.05:
            print("\n⚠ VCOM MISMATCH DETECTED!")
            print("This can cause:")
            print("- Poor contrast")
            print("- Ghosting")
            print("- Uneven updates")
            print("\nSolutions:")
            print("1. Use the correct VCOM value from your display's cable")
            print("2. Run vcom_calibration.py to find optimal value")
            print("3. Consider setting device VCOM to match specified value")
        else:
            print("✓ VCOM values match")

    except Exception as e:
        print(f"Failed to read VCOM: {e}")


def main() -> None:  # noqa: PLR0912, PLR0915
    """Main function."""
    parser = argparse.ArgumentParser(description="Troubleshooting and diagnostics demo")
    parser.add_argument(
        "-v", "--vcom", type=float, required=True, help="VCOM voltage value (e.g., -2.36)"
    )
    parser.add_argument("--quick", action="store_true", help="Run quick diagnostics only")

    args = parser.parse_args()

    print("=" * 60)
    print("IT8951 E-Paper Troubleshooting & Diagnostics")
    print("=" * 60)
    print(f"\nVCOM: {args.vcom}V")
    print("\nThis demo helps diagnose common issues.")

    try:
        with EPaperDisplay(vcom=args.vcom) as display:
            # Initialize display
            width, height = display.init()
            print(f"\nDisplay initialized: {width}x{height}")

            if args.quick:
                # Quick diagnostics
                print("\nRunning quick diagnostics...")
                diagnose_communication(display)
                check_vcom_mismatch(display, args.vcom)
            else:
                # Full diagnostics menu
                while True:
                    print("\n" + "=" * 60)
                    print("DIAGNOSTIC MENU")
                    print("=" * 60)
                    print("1. Communication diagnostics")
                    print("2. Display quality diagnostics")
                    print("3. Performance diagnostics")
                    print("4. Memory diagnostics")
                    print("5. Power management diagnostics")
                    print("6. VCOM configuration check")
                    print("7. Run all diagnostics")
                    print("0. Exit")

                    choice = input("\nSelect diagnostic (0-7): ")

                    if choice == "0":
                        break
                    if choice == "1":
                        diagnose_communication(display)
                    elif choice == "2":
                        diagnose_display_quality(display)
                    elif choice == "3":
                        diagnose_performance(display)
                    elif choice == "4":
                        diagnose_memory(display)
                    elif choice == "5":
                        diagnose_power_management(display)
                    elif choice == "6":
                        check_vcom_mismatch(display, args.vcom)
                    elif choice == "7":
                        # Run all
                        diagnose_communication(display)
                        diagnose_display_quality(display)
                        diagnose_performance(display)
                        diagnose_memory(display)
                        diagnose_power_management(display)
                        check_vcom_mismatch(display, args.vcom)
                    else:
                        print("Invalid choice")

                    if choice != "0":
                        input("\nPress Enter to continue...")

        print("\nDiagnostics completed!")

    except IT8951Error as e:
        print(f"\nFailed to initialize display: {e}")
        print("\nBasic troubleshooting:")
        print("1. Check all connections")
        print("2. Verify power supply")
        print("3. Enable SPI on Raspberry Pi")
        print("4. Check VCOM value")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nDiagnostics interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
