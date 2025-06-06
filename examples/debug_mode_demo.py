#!/usr/bin/env python3
"""Debug mode demonstration.

This example demonstrates how to use the debug mode features for troubleshooting
and development with the IT8951 driver.

Usage:
    python debug_mode_demo.py -v <VCOM_VALUE>

Example:
    python debug_mode_demo.py -v -2.36
"""

import argparse
import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PIL import Image, ImageDraw

from IT8951_ePaper_Py import (
    DebugLevel,
    EPaperDisplay,
    disable_debug,
    enable_debug,
    set_component_debug,
)
from IT8951_ePaper_Py.constants import DisplayMode


def demo_basic_debug() -> None:
    """Demonstrate basic debug mode usage."""
    print("\n1. BASIC DEBUG MODE")
    print("-" * 40)

    # Enable debug mode globally
    print("Enabling DEBUG level globally...")
    enable_debug(DebugLevel.DEBUG)

    # This will now show debug output
    display = EPaperDisplay(vcom=-2.0)
    display.close()

    # Disable debug mode
    print("\nDisabling debug mode...")
    disable_debug()

    # This won't show debug output
    display = EPaperDisplay(vcom=-2.0)
    display.close()


def demo_component_debug(vcom: float) -> None:
    """Demonstrate component-specific debug levels."""
    print("\n2. COMPONENT-SPECIFIC DEBUG")
    print("-" * 40)

    # Enable different levels for different components
    print("Setting component-specific debug levels:")
    print("  - SPI: TRACE (very verbose)")
    print("  - Display: INFO (general info only)")
    print("  - Power: DEBUG (detailed)")

    set_component_debug("spi", DebugLevel.TRACE)
    set_component_debug("display", DebugLevel.INFO)
    set_component_debug("power", DebugLevel.DEBUG)

    # Initialize display - will show different verbosity per component
    with EPaperDisplay(vcom=vcom) as display:
        width, height = display.init()
        print(f"\nDisplay size: {width}x{height}")


def demo_environment_variables() -> None:
    """Demonstrate environment variable configuration."""
    print("\n3. ENVIRONMENT VARIABLE CONFIGURATION")
    print("-" * 40)

    print("Debug mode can be configured via environment variables:")
    print("  IT8951_DEBUG=INFO                  # Global debug level")
    print("  IT8951_DEBUG_SPI=TRACE            # SPI component level")
    print("  IT8951_DEBUG_DISPLAY=DEBUG        # Display component level")

    # Set environment variables (for demonstration)
    os.environ["IT8951_DEBUG"] = "INFO"
    os.environ["IT8951_DEBUG_SPI"] = "DEBUG"

    # Create new display instance - will pick up env vars
    display = EPaperDisplay(vcom=-2.0)
    display.close()

    # Clean up
    del os.environ["IT8951_DEBUG"]
    del os.environ["IT8951_DEBUG_SPI"]


def demo_debug_levels(vcom: float) -> None:
    """Demonstrate different debug levels."""
    print("\n4. DEBUG LEVELS")
    print("-" * 40)

    levels = [
        (DebugLevel.OFF, "No output"),
        (DebugLevel.ERROR, "Only errors"),
        (DebugLevel.WARNING, "Warnings and errors"),
        (DebugLevel.INFO, "General information"),
        (DebugLevel.DEBUG, "Detailed debug info"),
        (DebugLevel.TRACE, "Very detailed trace info"),
    ]

    for level, description in levels:
        print(f"\n{level.name} - {description}:")
        enable_debug(level)

        # Perform a simple operation
        display = EPaperDisplay(vcom=vcom)
        if level >= DebugLevel.INFO:
            # Only init if we'll see some output
            display.init()
        display.close()

    # Reset to off
    disable_debug()


def demo_error_context(vcom: float) -> None:
    """Demonstrate enhanced error messages with context."""
    print("\n5. ENHANCED ERROR MESSAGES")
    print("-" * 40)

    # Enable error-level debugging
    enable_debug(DebugLevel.ERROR)

    try:
        # Try to use invalid VCOM (will show context in error)
        display = EPaperDisplay(vcom=-10.0)  # Invalid VCOM
        display.init()
    except Exception as e:
        print(f"Error with context: {e}")

    # Disable debug
    disable_debug()


def demo_performance_impact(vcom: float) -> None:
    """Demonstrate performance impact of debug levels."""
    print("\n6. PERFORMANCE IMPACT")
    print("-" * 40)

    import time

    # Create test image
    img = Image.new("L", (400, 300), 255)
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 350, 250], fill=128)

    # Test with debug OFF
    disable_debug()
    with EPaperDisplay(vcom=vcom) as display:
        display.init()

        start = time.time()
        display.display_image(img, mode=DisplayMode.DU)
        no_debug_time = time.time() - start
        print(f"Time with debug OFF: {no_debug_time:.3f}s")

    # Test with debug TRACE
    enable_debug(DebugLevel.TRACE)
    with EPaperDisplay(vcom=vcom) as display:
        display.init()

        start = time.time()
        display.display_image(img, mode=DisplayMode.DU)
        trace_debug_time = time.time() - start
        print(f"Time with debug TRACE: {trace_debug_time:.3f}s")
        print(f"Overhead: {trace_debug_time - no_debug_time:.3f}s")

    disable_debug()


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Debug mode demonstration")
    parser.add_argument(
        "-v", "--vcom", type=float, required=True, help="VCOM voltage value (e.g., -2.36)"
    )
    parser.add_argument("--basic-only", action="store_true", help="Only run basic debug demo")

    args = parser.parse_args()

    print("=" * 60)
    print("IT8951 E-Paper Debug Mode Demonstration")
    print("=" * 60)

    # Basic debug demo (doesn't need hardware)
    demo_basic_debug()

    if args.basic_only:
        print("\nBasic demo complete (--basic-only specified)")
        return

    # Component-specific debug
    demo_component_debug(args.vcom)

    # Environment variables
    demo_environment_variables()

    # Debug levels
    demo_debug_levels(args.vcom)

    # Error context
    demo_error_context(args.vcom)

    # Performance impact
    demo_performance_impact(args.vcom)

    print("\n" + "=" * 60)
    print("Debug mode demonstration complete!")
    print("\nTips:")
    print("- Use enable_debug() in your code for troubleshooting")
    print("- Set component-specific levels for targeted debugging")
    print("- Use environment variables for runtime configuration")
    print("- Remember to disable debug mode in production!")


if __name__ == "__main__":
    main()
