#!/usr/bin/env python3
"""Demo script for enhanced driving capability.

This example demonstrates when and how to use the enhanced driving
feature to improve display quality with long cables or blurry displays.
"""

import sys
import time

from IT8951_ePaper_Py import EPaperDisplay


def show_intro(vcom: float) -> None:
    """Show introduction and explanation."""
    print("Enhanced Driving Capability Demo")
    print("================================")

    # ⚠️ IMPORTANT: VCOM Configuration ⚠️
    print(f"\nUsing VCOM voltage: {vcom}V")
    print("   Make sure this matches your display's FPC cable!")

    print("\nEnhanced driving improves signal quality and can help with:")
    print("- Blurry or unclear display output")
    print("- Long FPC cable connections")
    print("- Display instability issues\n")


def demo_standard_init(vcom: float) -> None:
    """Demonstrate standard initialization."""
    print("Example 1: Standard initialization")
    print("-" * 40)
    display = EPaperDisplay(vcom=vcom)
    width, height = display.init()
    print(f"Display initialized: {width}x{height}")
    display.close()
    print()


def demo_enhanced_init(vcom: float) -> EPaperDisplay:
    """Demonstrate initialization with enhanced driving."""
    print("Example 2: Initialization with enhanced driving")
    print("-" * 40)
    display = EPaperDisplay(
        vcom=vcom,
        enhance_driving=True,  # Enable enhanced driving
    )
    width, height = display.init()
    print(f"Display initialized with enhanced driving: {width}x{height}")
    print("Enhanced driving is now active!\n")
    return display


def show_usage_guide() -> None:
    """Show when to use enhanced driving."""
    print("When to use enhanced driving:")
    print("1. If your display appears blurry or unclear")
    print("2. If you're using a long FPC cable (>10cm)")
    print("3. If you see display instability or artifacts")
    print("4. If text appears fuzzy or lines are not sharp")
    print("\nNote: Enhanced driving may slightly increase power consumption")
    print("      but significantly improves display quality in problem cases.\n")


def show_diagnostics(display: EPaperDisplay) -> None:
    """Show diagnostic information."""
    print("Diagnostic information:")
    print("-" * 40)

    # Check if enhanced driving is actually enabled
    if display.is_enhanced_driving_enabled():
        print("✓ Enhanced driving is ENABLED")
    else:
        print("✗ Enhanced driving is DISABLED")

    try:
        # Dump registers to see the enhanced driving state
        registers = display.dump_registers()
        print("\nRegister dump:")
        for name, value in registers.items():
            status = "(ENABLED)" if name == "ENHANCE_DRIVING" and value == 0x0602 else ""
            if name == "ENHANCE_DRIVING" and value != 0x0602:
                status = "(DISABLED)"
            print(f"  {name}: 0x{value:04X} {status}")
    except Exception as e:
        print(f"Could not read registers: {e}")


def main() -> None:
    """Demonstrate enhanced driving capability."""
    if len(sys.argv) < 2:
        print("Usage: python enhanced_driving_demo.py <vcom_voltage>")
        print("Example: python enhanced_driving_demo.py -1.45")
        print("\n⚠️  IMPORTANT: The VCOM voltage MUST match your display's specification!")
        print("   Check the FPC cable on your display for the correct VCOM value.")
        sys.exit(1)

    vcom = float(sys.argv[1])
    show_intro(vcom)

    # Example 1: Standard initialization
    demo_standard_init(vcom)

    # Wait between initializations
    time.sleep(1)

    # Example 2: Enhanced initialization
    display_enhanced = demo_enhanced_init(vcom)

    # Show usage guide
    show_usage_guide()

    # Show diagnostics
    show_diagnostics(display_enhanced)

    # Clean up
    display_enhanced.close()
    print("\nDemo complete!")


if __name__ == "__main__":
    main()
