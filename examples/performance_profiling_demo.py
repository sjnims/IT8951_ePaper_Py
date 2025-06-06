#!/usr/bin/env python3
"""Performance profiling example for IT8951 e-paper driver.

This example demonstrates how to profile and measure performance of various
operations to identify bottlenecks and optimize your e-paper applications.
"""

import cProfile
import pstats
import time
from collections.abc import Generator
from contextlib import contextmanager
from io import StringIO

import numpy as np
from PIL import Image

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode, PixelFormat
from IT8951_ePaper_Py.it8951 import IT8951
from IT8951_ePaper_Py.pixel_packing import pack_pixels_numpy
from IT8951_ePaper_Py.spi_interface import create_spi_interface


@contextmanager
def timer(name: str) -> Generator[None, None, None]:
    """Simple context manager for timing operations."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"{name}: {elapsed:.3f} seconds")


def profile_pixel_packing() -> None:
    """Profile different pixel packing implementations."""
    print("\n=== Pixel Packing Performance ===")

    # Test data sizes
    sizes = [1000, 10000, 100000, 1000000]

    for size in sizes:
        print(f"\n--- Size: {size:,} pixels ---")

        # Generate test data
        pixels = np.random.randint(0, 256, size=size, dtype=np.uint8)
        pixels_bytes = pixels.tobytes()

        # Test different formats
        for format_name, pixel_format in [
            ("8bpp", PixelFormat.BPP_8),
            ("4bpp", PixelFormat.BPP_4),
            ("2bpp", PixelFormat.BPP_2),
            ("1bpp", PixelFormat.BPP_1),
        ]:
            # Test standard implementation
            with timer(f"Standard {format_name}"):
                _ = IT8951.pack_pixels(pixels_bytes, pixel_format)

            # Test numpy implementation (if large enough)
            if size >= 10000:
                with timer(f"Numpy {format_name}"):
                    _ = pack_pixels_numpy(pixels, pixel_format)


def profile_spi_operations() -> None:
    """Profile SPI communication operations."""
    print("\n=== SPI Communication Performance ===")

    # Create SPI interface (will be MockSPI on non-Pi systems)
    spi = create_spi_interface()
    spi.init()

    # Test write operations
    test_data = list(range(1000))

    print("\n--- Write Operations ---")

    # Single writes
    with timer("1000 single writes"):
        for value in test_data:
            spi.write_data(value)

    # Bulk write
    with timer("1 bulk write (1000 values)"):
        spi.write_data_bulk(test_data)

    # Test read operations
    print("\n--- Read Operations ---")

    # Single reads
    with timer("1000 single reads"):
        for _ in range(1000):
            _ = spi.read_data()

    # Bulk read
    with timer("1 bulk read (1000 values)"):
        _ = spi.read_data_bulk(1000)

    spi.close()


def profile_display_operations() -> None:
    """Profile display operations with different modes and formats."""
    print("\n=== Display Operations Performance ===")

    # Create display (will use MockSPI on non-Pi systems)
    display = EPaperDisplay(vcom=-2.0)
    _ = display.init()  # Initialize but don't need dimensions for this test

    # Create test images
    test_sizes = [(200, 200), (400, 400), (800, 600)]

    for w, h in test_sizes:
        print(f"\n--- Image Size: {w}x{h} ---")

        # Create a test image
        img = Image.new("L", (w, h))
        pixels = np.random.randint(0, 256, size=(h, w), dtype=np.uint8)
        img.putdata(pixels.flatten().tolist())

        # Test different pixel formats
        for format_name, pixel_format in [
            ("4bpp", PixelFormat.BPP_4),
            ("2bpp", PixelFormat.BPP_2),
            ("1bpp", PixelFormat.BPP_1),
        ]:
            with timer(f"Display {format_name}"):
                display.display_image(
                    img, x=0, y=0, mode=DisplayMode.GL16, pixel_format=pixel_format
                )

    display.close()


def profile_with_cprofile() -> None:
    """Use cProfile for detailed profiling."""
    print("\n=== Detailed Profile with cProfile ===")

    # Create a profiler
    pr = cProfile.Profile()

    # Profile some operations
    pr.enable()

    # Simulate typical usage
    pixels = np.random.randint(0, 256, size=100000, dtype=np.uint8)
    pixels_bytes = pixels.tobytes()

    # Pack pixels multiple times
    for _ in range(10):
        _ = IT8951.pack_pixels(pixels_bytes, PixelFormat.BPP_4)
        _ = pack_pixels_numpy(pixels, PixelFormat.BPP_4)

    pr.disable()

    # Print statistics
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(20)  # Top 20 functions

    print(s.getvalue())


def memory_profiling() -> None:
    """Profile memory usage patterns."""
    print("\n=== Memory Usage Profiling ===")

    import gc
    import sys

    # Test memory allocation patterns
    sizes = [1000, 10000, 100000]

    for size in sizes:
        # Force garbage collection
        gc.collect()

        # Get initial memory
        initial_objects = len(gc.get_objects())

        # Allocate and pack pixels
        pixels = np.random.randint(0, 256, size=size, dtype=np.uint8)
        packed = IT8951.pack_pixels(pixels.tobytes(), PixelFormat.BPP_4)

        # Get final memory
        final_objects = len(gc.get_objects())

        print(f"\nSize: {size:,} pixels")
        print(f"  Input size: {sys.getsizeof(pixels):,} bytes")
        print(f"  Output size: {sys.getsizeof(packed):,} bytes")
        print(f"  Objects created: {final_objects - initial_objects}")
        print(f"  Compression ratio: {len(pixels) / len(packed):.1f}:1")


def main() -> None:
    """Run all profiling examples."""
    print("IT8951 E-Paper Driver Performance Profiling")
    print("=" * 50)

    # Run profiling tests
    profile_pixel_packing()
    profile_spi_operations()
    profile_display_operations()
    profile_with_cprofile()
    memory_profiling()

    print("\n" + "=" * 50)
    print("Profiling complete!")
    print("\nTips for optimizing performance:")
    print("1. Use 4bpp format for best balance of quality and speed")
    print("2. Use numpy-based packing for large images (>10k pixels)")
    print("3. Use bulk SPI operations instead of single transfers")
    print("4. Pre-allocate buffers for repeated operations")
    print("5. Consider using the buffer pool for memory efficiency")


if __name__ == "__main__":
    main()
