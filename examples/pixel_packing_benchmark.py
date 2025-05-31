#!/usr/bin/env python3
"""Pixel packing performance benchmark.

This example demonstrates the performance improvements achieved by using
numpy-optimized pixel packing functions for different bit depths.
"""

import time

import numpy as np
from PIL import Image

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode, PixelFormat
from IT8951_ePaper_Py.it8951 import IT8951
from IT8951_ePaper_Py.pixel_packing import pack_pixels_numpy


def benchmark_packing_methods(image_sizes: list[tuple[int, int]]) -> None:
    """Benchmark different pixel packing methods.

    Args:
        image_sizes: List of (width, height) tuples to test.
    """
    print("Pixel Packing Performance Benchmark")
    print("=" * 50)

    for width, height in image_sizes:
        print(f"\nImage size: {width}x{height} ({width * height:,} pixels)")
        print("-" * 40)

        # Create test data
        num_pixels = width * height
        test_data = np.random.randint(0, 256, num_pixels, dtype=np.uint8)
        test_bytes = test_data.tobytes()

        # Test each pixel format
        for pixel_format in [PixelFormat.BPP_4, PixelFormat.BPP_2, PixelFormat.BPP_1]:
            print(f"\n{pixel_format.name}:")

            # Benchmark original implementation
            start = time.perf_counter()
            result_original = IT8951.pack_pixels(test_bytes, pixel_format)
            time_original = time.perf_counter() - start

            # Benchmark numpy implementation (direct call)
            start = time.perf_counter()
            result_numpy = pack_pixels_numpy(test_data, pixel_format)
            time_numpy = time.perf_counter() - start

            # Verify results match
            if result_original != result_numpy:
                print("  WARNING: Results don't match!")

            # Calculate speedup
            speedup = time_original / time_numpy if time_numpy > 0 else 0

            print(f"  Original: {time_original * 1000:6.2f} ms")
            print(f"  NumPy:    {time_numpy * 1000:6.2f} ms")
            print(f"  Speedup:  {speedup:6.1f}x")

            # Calculate throughput
            mb_per_sec_original = (num_pixels / 1024 / 1024) / time_original
            mb_per_sec_numpy = (num_pixels / 1024 / 1024) / time_numpy
            print(f"  Throughput (original): {mb_per_sec_original:6.1f} MB/s")
            print(f"  Throughput (numpy):    {mb_per_sec_numpy:6.1f} MB/s")


def benchmark_real_world_usage(display: EPaperDisplay) -> None:
    """Benchmark real-world image display with different methods.

    Args:
        display: Initialized EPaperDisplay instance.
    """
    print("\n\nReal-World Display Performance")
    print("=" * 50)

    # Create test images of different sizes
    test_cases = [
        ("Small", 400, 300),
        ("Medium", 800, 600),
        ("Large", 1600, 1200),
    ]

    for name, width, height in test_cases:
        print(f"\n{name} image ({width}x{height}):")
        print("-" * 40)

        # Create gradient test image
        img = Image.new("L", (width, height))
        # Generate pixels with explicit typing for PIL compatibility
        # PIL expects Sequence[float] for grayscale images
        pixels: list[float] = [
            float((x + y) * 255 / (width + height)) for y in range(height) for x in range(width)
        ]
        # Note: PIL's putdata() type annotations include Unknown in the union type,
        # causing pyright to warn. Our usage is correct, so we suppress the warning.
        img.putdata(pixels)  # type: ignore[reportUnknownMemberType]

        # Test each pixel format
        for pixel_format in [PixelFormat.BPP_4, PixelFormat.BPP_2, PixelFormat.BPP_1]:
            print(f"\n  {pixel_format.name}:")

            # Time the entire display operation
            start = time.perf_counter()
            display.display_image(
                img,
                x=(display.width - width) // 2,
                y=(display.height - height) // 2,
                mode=DisplayMode.GC16,
                pixel_format=pixel_format,
            )
            total_time = time.perf_counter() - start

            print(f"    Total display time: {total_time * 1000:.1f} ms")

            # Calculate effective data rate
            if pixel_format == PixelFormat.BPP_4:
                packed_size = (width * height) // 2
            elif pixel_format == PixelFormat.BPP_2:
                packed_size = (width * height) // 4
            elif pixel_format == PixelFormat.BPP_1:
                packed_size = (width * height) // 8
            else:
                packed_size = width * height

            data_rate = (packed_size / 1024 / 1024) / total_time
            print(f"    Effective data rate: {data_rate:.1f} MB/s")


def main() -> None:
    """Run pixel packing benchmarks."""
    # Benchmark pure packing performance
    image_sizes = [
        (400, 300),  # Small
        (800, 600),  # Medium
        (1024, 768),  # XGA
        (1600, 1200),  # UXGA
        (2048, 1536),  # QXGA
    ]

    benchmark_packing_methods(image_sizes)

    # Optional: benchmark with real display
    try:
        print("\n\nInitializing display for real-world benchmark...")
        display = EPaperDisplay(vcom=-2.0)  # Adjust VCOM for your display
        display.init()

        benchmark_real_world_usage(display)

        display.close()
    except Exception as e:
        print(f"\nSkipping real-world benchmark: {e}")
        print("(This is normal when running without hardware)")


if __name__ == "__main__":
    main()
