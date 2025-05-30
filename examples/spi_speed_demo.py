#!/usr/bin/env python3
"""Demo script for SPI speed configuration.

This example demonstrates the new auto-detection and manual override
features for SPI speed configuration based on Raspberry Pi version.
"""

import sys

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.spi_interface import detect_raspberry_pi_version, get_spi_speed_for_pi


def main() -> None:
    """Demonstrate SPI speed configuration options."""
    if len(sys.argv) < 2:
        print("Usage: python spi_speed_demo.py <vcom_voltage>")
        print("Example: python spi_speed_demo.py -1.45")
        print("\n⚠️  IMPORTANT: The VCOM voltage MUST match your display's specification!")
        print("   Check the FPC cable on your display for the correct VCOM value.")
        sys.exit(1)

    vcom = float(sys.argv[1])
    print(f"Using VCOM voltage: {vcom}V\n")

    # Detect Pi version (will return 4 on non-Pi systems)
    pi_version = detect_raspberry_pi_version()
    print(f"Detected Raspberry Pi version: {pi_version}")

    # Get recommended speed for detected Pi
    recommended_speed = get_spi_speed_for_pi()
    print(
        f"Recommended SPI speed: {recommended_speed:,} Hz ({recommended_speed / 1_000_000:.3f} MHz)"
    )

    # Example 1: Auto-detect Pi version and use appropriate speed
    print("\nExample 1: Auto-detection (recommended)")
    display = EPaperDisplay(vcom=vcom)  # Auto-detects Pi and sets speed
    print("Display initialized with auto-detected SPI speed")
    display.close()  # Clean up

    # Example 2: Manual speed override for testing
    print("\nExample 2: Manual speed override")
    custom_speed = 10_000_000  # 10 MHz
    display = EPaperDisplay(vcom=vcom, spi_speed_hz=custom_speed)
    print(f"Display initialized with custom SPI speed: {custom_speed:,} Hz")
    display.close()  # Clean up

    # Example 3: Show speed recommendations
    print("\nSPI Speed Recommendations:")
    print("- Raspberry Pi 1-3: 15.625 MHz (faster)")
    print("- Raspberry Pi 4-5: 7.8125 MHz (more stable)")
    print("- Unknown/Other: 7.8125 MHz (conservative)")

    print("\nNote: These speeds are based on Waveshare's recommendations.")
    print("Pi 4+ requires slower speeds due to hardware differences.")


if __name__ == "__main__":
    main()
