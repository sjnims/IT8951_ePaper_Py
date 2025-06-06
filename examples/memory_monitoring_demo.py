#!/usr/bin/env python3
"""Memory monitoring demonstration for IT8951 e-paper driver.

This example shows how to monitor and optimize memory usage during
e-paper display operations using the built-in memory monitoring tools.
"""

import numpy as np
from PIL import Image

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.buffer_pool import BufferPool, ManagedBuffer
from IT8951_ePaper_Py.constants import PixelFormat
from IT8951_ePaper_Py.it8951 import IT8951
from IT8951_ePaper_Py.memory_monitor import (
    MemoryMonitor,
    estimate_memory_usage,
    get_memory_stats,
    monitor_memory,
)


def demonstrate_basic_monitoring() -> None:
    """Demonstrate basic memory monitoring."""
    print("\n=== Basic Memory Monitoring ===")

    monitor = MemoryMonitor()
    monitor.start_tracking()

    # Take initial snapshot
    monitor.take_snapshot("Initial")

    # Allocate some memory
    data = np.random.randint(0, 256, size=(1000, 1000), dtype=np.uint8)
    monitor.take_snapshot("After 1MB allocation")

    # Process the data
    packed = IT8951.pack_pixels(data.tobytes(), PixelFormat.BPP_4)
    monitor.take_snapshot("After packing to 4bpp")

    # Clean up
    del data
    del packed
    monitor.take_snapshot("After cleanup")

    # Print summary
    monitor.print_summary()
    monitor.stop_tracking()


def demonstrate_context_manager() -> None:
    """Demonstrate memory monitoring with context manager."""
    print("\n=== Context Manager Memory Monitoring ===")

    with monitor_memory("Image Processing") as monitor:
        # Simulate image processing
        img = Image.new("L", (800, 600), 128)
        monitor.take_snapshot("After image creation")

        # Convert to numpy
        arr = np.array(img)
        monitor.take_snapshot("After numpy conversion")

        # Pack pixels
        _ = IT8951.pack_pixels(arr.tobytes(), PixelFormat.BPP_2)
        monitor.take_snapshot("After 2bpp packing")

        # The summary is printed automatically on exit


def demonstrate_memory_estimation() -> None:
    """Demonstrate memory usage estimation."""
    print("\n=== Memory Usage Estimation ===")

    # Common display sizes
    sizes = [
        (800, 600, "Small display"),
        (1024, 768, "Medium display"),
        (1872, 1404, "10.3 inch"),
        (2048, 2048, "Maximum size"),
    ]

    for width, height, name in sizes:
        print(f"\n{name} ({width}x{height}):")

        for pixel_format, format_name in [
            (PixelFormat.BPP_1, "1bpp"),
            (PixelFormat.BPP_2, "2bpp"),
            (PixelFormat.BPP_4, "4bpp"),
            (PixelFormat.BPP_8, "8bpp"),
        ]:
            estimate = estimate_memory_usage(width, height, pixel_format)
            print(
                f"  {format_name}: {estimate['total_mb']:.1f}MB "
                f"(compression: {estimate['compression_ratio']:.1f}:1)"
            )


def demonstrate_buffer_pool_monitoring() -> None:
    """Demonstrate memory usage with and without buffer pool."""
    print("\n=== Buffer Pool Memory Comparison ===")

    # Clear any existing pools
    BufferPool.clear_pools()

    # Without buffer pool
    with monitor_memory("Without Buffer Pool") as monitor:
        for i in range(10):
            # Allocate new buffer each time
            buffer = bytes(1024 * 1024)  # 1MB
            # Simulate processing
            _ = sum(buffer) / len(buffer)
            monitor.take_snapshot(f"Iteration {i + 1}")

    # With buffer pool
    with monitor_memory("With Buffer Pool") as monitor:
        for i in range(10):
            # Use buffer pool
            with ManagedBuffer.bytes(1024 * 1024) as buffer:
                # Simulate processing
                _ = sum(buffer) / len(buffer)
            monitor.take_snapshot(f"Iteration {i + 1}")

    print("\nNote: Buffer pool reuses memory, reducing allocations")


def demonstrate_memory_leak_detection() -> None:
    """Demonstrate how to detect memory leaks."""
    print("\n=== Memory Leak Detection ===")

    monitor = MemoryMonitor()
    monitor.start_tracking()

    # Baseline
    initial_stats = get_memory_stats()
    monitor.take_snapshot("Baseline")

    # Simulate operations that might leak
    leaked_objects = []
    for i in range(5):
        # This simulates a leak by keeping references
        data = np.random.randint(0, 256, size=(100, 100), dtype=np.uint8)
        leaked_objects.append(data)  # Leak: keeping reference

        current_stats = get_memory_stats()
        objects_delta = current_stats["python"]["objects"] - initial_stats["python"]["objects"]

        print(f"Iteration {i + 1}: {objects_delta:+} objects")
        monitor.take_snapshot(f"Iteration {i + 1}")

    monitor.print_summary()

    # Show top allocations
    print("\nTop Memory Allocations:")
    for line in monitor.get_top_allocations(5):
        print(f"  {line}")

    monitor.stop_tracking()


def demonstrate_display_memory_usage() -> None:
    """Demonstrate memory usage during display operations."""
    print("\n=== Display Operation Memory Usage ===")

    # Create display with mock SPI
    display = EPaperDisplay(vcom=-2.0)

    with monitor_memory("Display Operations") as monitor:
        # Initialize
        _ = display.init()  # Returns (width, height)
        monitor.take_snapshot("After init")

        # Create test image
        img = Image.new("L", (400, 300), 255)
        monitor.take_snapshot("After image creation")

        # Display with different formats
        for pixel_format, name in [
            (PixelFormat.BPP_4, "4bpp"),
            (PixelFormat.BPP_2, "2bpp"),
            (PixelFormat.BPP_1, "1bpp"),
        ]:
            display.display_image(img, pixel_format=pixel_format)
            monitor.take_snapshot(f"After {name} display")

    display.close()


def demonstrate_progressive_loading() -> None:
    """Demonstrate memory-efficient progressive loading."""
    print("\n=== Progressive Loading Memory Usage ===")

    # Large image dimensions
    width, height = 2048, 1536

    with monitor_memory("Progressive Loading") as monitor:
        # Chunk size for progressive loading
        chunk_height = 256

        # Process in chunks to minimize memory usage
        for y in range(0, height, chunk_height):
            # Only load/create what we need
            chunk_h = min(chunk_height, height - y)
            chunk = np.random.randint(0, 256, size=(chunk_h, width), dtype=np.uint8)

            # Pack the chunk
            packed = IT8951.pack_pixels(chunk.tobytes(), PixelFormat.BPP_4)

            # Simulate sending to display
            # display.display_partial(packed, 0, y, width, chunk_h)

            # Clean up immediately
            del chunk
            del packed

            if y == 0:
                monitor.take_snapshot("After first chunk")

        monitor.take_snapshot("After all chunks")

    print(f"\nProcessed {width}x{height} image in {height // chunk_height} chunks")
    print("Peak memory usage is limited to chunk size, not full image size")


def main() -> None:
    """Run all memory monitoring demonstrations."""
    print("IT8951 E-Paper Driver - Memory Monitoring Demo")
    print("=" * 50)

    # Get initial system stats
    stats = get_memory_stats()
    print(
        f"\nSystem Memory: {stats['system']['available_mb']:.1f}MB available "
        f"of {stats['system']['total_mb']:.1f}MB total"
    )
    print(f"Process Memory: {stats['process']['rss_mb']:.1f}MB RSS")

    # Run demonstrations
    demonstrate_basic_monitoring()
    demonstrate_context_manager()
    demonstrate_memory_estimation()
    demonstrate_buffer_pool_monitoring()
    demonstrate_memory_leak_detection()
    demonstrate_display_memory_usage()
    demonstrate_progressive_loading()

    # Final stats
    final_stats = get_memory_stats()
    print("\n" + "=" * 50)
    print("Final Memory Statistics:")
    print(f"  RSS Change: {final_stats['process']['rss_mb'] - stats['process']['rss_mb']:+.1f}MB")
    print(f"  Python Objects: {final_stats['python']['objects']:,}")
    print(f"  Garbage Objects: {final_stats['python']['garbage']}")

    print("\nMemory Monitoring Tips:")
    print("1. Use buffer pools to reuse memory allocations")
    print("2. Process large images in chunks (progressive loading)")
    print("3. Use appropriate pixel formats (4bpp uses 50% less than 8bpp)")
    print("4. Clean up references promptly to allow garbage collection")
    print("5. Monitor peak memory usage, not just current usage")


if __name__ == "__main__":
    main()
