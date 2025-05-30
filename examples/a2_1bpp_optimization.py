#!/usr/bin/env python3
"""Demonstrate optimized A2 mode with 1bpp for ultra-fast binary updates.

This example shows how combining A2 mode with 1bpp provides the fastest
possible refresh rates for binary content. A2 mode is inherently binary
(black/white only), making it a perfect match for 1bpp data.

Performance benefits of A2 + 1bpp:
- A2 mode: ~120ms refresh (fastest mode)
- 1bpp: 1/8th the data of 8bpp
- Combined: Minimal data transfer + fastest refresh
- Perfect for real-time displays, clocks, status indicators
"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode, PixelFormat

logger = logging.getLogger(__name__)


def create_clock_display(width: int, height: int) -> Image.Image:
    """Create a digital clock display."""
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    # Get current time
    current_time = datetime.now().strftime("%H:%M:%S")

    # Try to use a large font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
    except Exception:
        font = ImageFont.load_default()

    # Calculate text position for centering
    bbox = draw.textbbox((0, 0), current_time, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # Draw the time
    draw.text((x, y), current_time, fill=0, font=font)

    # Add date below
    try:
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except Exception:
        small_font = ImageFont.load_default()

    date_str = datetime.now().strftime("%A, %B %d, %Y")
    bbox = draw.textbbox((0, 0), date_str, font=small_font)
    date_width = bbox[2] - bbox[0]
    x = (width - date_width) // 2
    y = y + text_height + 50

    draw.text((x, y), date_str, fill=0, font=small_font)

    return img


def create_status_display(width: int, height: int, status_data: dict[str, bool]) -> Image.Image:
    """Create a status display with various indicators."""
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except Exception:
        font = ImageFont.load_default()

    # Title
    draw.text((20, 20), "System Status", fill=0, font=font)

    # Status indicators
    y_offset = 80
    for key, value in status_data.items():
        # Draw status box
        box_color = 0 if value else 255  # Black if true, white if false
        draw.rectangle([20, y_offset, 40, y_offset + 20], fill=box_color, outline=0)

        # Draw label
        draw.text((60, y_offset), key, fill=0, font=font)

        y_offset += 40

    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw.text((20, height - 50), f"Updated: {timestamp}", fill=0, font=font)

    return img


def benchmark_modes(display: EPaperDisplay, test_image: Image.Image) -> dict[str, float]:
    """Benchmark different mode and pixel format combinations."""
    results: dict[str, float] = {}

    # Test combinations
    tests = [
        ("A2 + 1bpp", DisplayMode.A2, PixelFormat.BPP_1),
        ("A2 + 4bpp", DisplayMode.A2, PixelFormat.BPP_4),
        ("DU + 1bpp", DisplayMode.DU, PixelFormat.BPP_1),
        ("GC16 + 1bpp", DisplayMode.GC16, PixelFormat.BPP_1),
    ]

    for name, mode, pixel_format in tests:
        print(f"\nTesting {name}...")
        start_time = time.time()

        display.display_image(test_image, mode=mode, pixel_format=pixel_format)

        elapsed = time.time() - start_time
        results[name] = elapsed
        print(f"{name}: {elapsed:.3f}s")

        time.sleep(1)  # Brief pause between tests

    return results


def run_clock_demo(display: EPaperDisplay, width: int, height: int, duration: int) -> None:
    """Run the real-time clock demo."""
    print("\n=== Real-time Clock Demo (A2 + 1bpp) ===")
    print("Watch the ultra-fast updates!")
    print(f"Running for {duration} seconds...")

    start_time = time.time()
    frame_count = 0

    while time.time() - start_time < duration:
        clock_img = create_clock_display(width, height)
        display.display_image(clock_img, mode=DisplayMode.A2, pixel_format=PixelFormat.BPP_1)
        frame_count += 1
        time.sleep(0.1)  # Small delay to avoid overwhelming the display

    elapsed = time.time() - start_time
    fps = frame_count / elapsed
    print(f"\nClock demo complete: {frame_count} frames in {elapsed:.1f}s = {fps:.1f} FPS")


def run_status_demo(display: EPaperDisplay, width: int, height: int) -> None:
    """Run the status display demo."""
    print("\n=== Status Display Demo (A2 + 1bpp) ===")
    print("Simulating real-time status updates...")

    # Simulate changing status
    for i in range(5):
        status_data = {
            "Network": i % 2 == 0,
            "Database": i % 3 != 0,
            "API": True,
            "Cache": i % 2 == 1,
            "Queue": i % 4 < 2,
        }

        status_img = create_status_display(width, height, status_data)
        display.display_image(status_img, mode=DisplayMode.A2, pixel_format=PixelFormat.BPP_1)

        time.sleep(1)


def run_benchmark_demo(display: EPaperDisplay, width: int, height: int) -> None:
    """Run the performance benchmark demo."""
    print("\n=== Performance Benchmark ===")
    print("Comparing different mode and pixel format combinations...")

    # Create a test pattern
    test_img = create_clock_display(width, height)

    results = benchmark_modes(display, test_img)

    print("\n=== Benchmark Results ===")
    sorted_results = sorted(results.items(), key=lambda x: x[1])
    for name, elapsed in sorted_results:
        print(f"{name:15} {elapsed:.3f}s")

    # Calculate speedup
    if "A2 + 1bpp" in results and "GC16 + 1bpp" in results:
        speedup = results["GC16 + 1bpp"] / results["A2 + 1bpp"]
        print(f"\nA2+1bpp is {speedup:.1f}x faster than GC16+1bpp")


def main() -> None:
    """Run the A2 + 1bpp optimization demo."""
    parser = argparse.ArgumentParser(description="A2 mode + 1bpp optimization demo")
    parser.add_argument("vcom", type=float, help="VCOM voltage (e.g., -2.0)")
    parser.add_argument(
        "--demo",
        choices=["clock", "status", "benchmark", "all"],
        default="all",
        help="Demo mode to run",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Duration for clock demo in seconds",
    )
    args = parser.parse_args()

    # Enable debug logging to see performance metrics
    logging.basicConfig(level=logging.DEBUG)

    print(f"Initializing display with VCOM={args.vcom}V...")
    display = EPaperDisplay(vcom=args.vcom)

    try:
        width, height = display.init()
        print(f"Display initialized: {width}x{height}")

        if args.demo in {"clock", "all"}:
            run_clock_demo(display, width, height, args.duration)
            if args.demo == "all":
                input("\nPress Enter to continue to status demo...")

        if args.demo in {"status", "all"}:
            run_status_demo(display, width, height)
            if args.demo == "all":
                input("\nPress Enter to continue to benchmark...")

        if args.demo in {"benchmark", "all"}:
            run_benchmark_demo(display, width, height)

        print("\n=== Why A2 + 1bpp is Optimal for Binary Content ===")
        print("• A2 mode is already binary (no grayscale processing needed)")
        print("• 1bpp matches A2's binary nature perfectly")
        print("• Minimal data transfer (1/8th of 8bpp)")
        print("• No wasted bits or processing on grayscale levels")
        print("• Ideal for: clocks, counters, status displays, text")

    finally:
        display.close()
        print("\nDisplay closed.")


if __name__ == "__main__":
    main()
