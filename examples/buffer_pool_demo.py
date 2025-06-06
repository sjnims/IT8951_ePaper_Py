#!/usr/bin/env python3
"""Buffer Pool Demo - Memory allocation optimization for e-paper operations.

This example demonstrates the buffer pool functionality in the IT8951 driver,
showing how to efficiently reuse memory allocations for better performance
in e-paper display operations.

The buffer pool is particularly useful for:
- Repeated display clearing operations
- Image format conversions
- Partial update buffer management
- Multi-threaded display operations
"""

import gc
import sys
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

# Add src to path for examples
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from IT8951_ePaper_Py.buffer_pool import BufferPool, ManagedBuffer


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"{title:^60}")
    print(f"{'=' * 60}\n")


def demo_basic_bytes_buffer() -> None:
    """Demonstrate basic bytes buffer usage."""
    print_section("Basic Bytes Buffer Usage")

    # Clear any existing pools
    BufferPool.clear_pools()

    # Get a buffer from the pool
    buffer_size = 1024 * 1024  # 1MB buffer (common for display clearing)
    buffer1 = BufferPool.get_bytes_buffer(buffer_size)
    print(f"Allocated buffer of size: {len(buffer1):,} bytes")

    # Return it to the pool
    BufferPool.return_bytes_buffer(buffer1)
    print("Buffer returned to pool")

    # Get another buffer - should reuse the pooled one
    buffer2 = BufferPool.get_bytes_buffer(buffer_size)
    print(f"Got buffer from pool: {buffer1 is buffer2}")

    # Get a buffer with specific fill value (creates new buffer)
    buffer3 = BufferPool.get_bytes_buffer(buffer_size, fill_value=0xFF)
    print(f"Created new buffer with fill value: {buffer3[0]:#04x}")

    # Clean up
    BufferPool.clear_pools()


def demo_numpy_array_buffer() -> None:
    """Demonstrate numpy array buffer pooling."""
    print_section("Numpy Array Buffer Pooling")

    # Clear any existing pools
    BufferPool.clear_pools()

    # Common e-paper display dimensions
    width, height = 1872, 1404  # 10.3" display at 227 DPI
    shape = (height, width)

    # Get an array buffer for display data
    display_buffer1 = BufferPool.get_array_buffer(shape, dtype=np.uint8)
    print(f"Allocated display buffer: {display_buffer1.shape}, dtype: {display_buffer1.dtype}")
    print(f"Buffer size: {display_buffer1.nbytes:,} bytes")

    # Fill with white (0xFF for e-paper)
    display_buffer1.fill(0xFF)

    # Return to pool
    BufferPool.return_array_buffer(display_buffer1)
    print("Display buffer returned to pool")

    # Get another buffer - should reuse if available
    display_buffer2 = BufferPool.get_array_buffer(shape, dtype=np.uint8)
    print(f"Buffer reused from pool: {display_buffer1 is display_buffer2}")

    # Get buffer with different dtype
    float_buffer = BufferPool.get_array_buffer(shape, dtype=np.float32)
    print(f"Float buffer allocated: dtype={float_buffer.dtype}, size={float_buffer.nbytes:,} bytes")

    # Clean up
    BufferPool.clear_pools()


def demo_managed_buffer_context() -> None:
    """Demonstrate ManagedBuffer context manager usage."""
    print_section("ManagedBuffer Context Manager")

    # Clear any existing pools
    BufferPool.clear_pools()

    # Using ManagedBuffer for automatic cleanup
    buffer_size = 512 * 1024  # 512KB

    # Bytes buffer with context manager
    print("Using managed bytes buffer:")
    with ManagedBuffer.bytes(buffer_size, fill_value=0x00) as buffer:
        print(f"  Buffer size: {len(buffer):,} bytes")
        print(f"  First byte: {buffer[0]:#04x}")
        # Buffer automatically returned to pool on exit

    # Check that buffer was returned to pool
    test_buffer = BufferPool.get_bytes_buffer(buffer_size)
    # Note: Can't directly check pool contents without accessing private members
    print("  Buffer was returned to pool")
    BufferPool.return_bytes_buffer(test_buffer)

    # Array buffer with context manager
    print("\nUsing managed array buffer:")
    shape = (100, 100)
    with ManagedBuffer.array(shape, dtype=np.uint16, fill_value=4095) as arr:
        print(f"  Array shape: {arr.shape}")
        print(f"  Array dtype: {arr.dtype}")
        print(f"  Array max value: {arr.max()}")
        # Array automatically returned to pool on exit

    # Clean up
    BufferPool.clear_pools()


def demo_performance_comparison() -> None:
    """Compare performance of pooled vs non-pooled allocations."""
    print_section("Performance Comparison: Pooled vs Non-Pooled")

    # Clear any existing pools
    BufferPool.clear_pools()

    # Test parameters
    buffer_size = 2 * 1024 * 1024  # 2MB (typical for full display update)
    iterations = 100

    # Non-pooled allocation timing
    print("Non-pooled allocation:")
    start_time = time.perf_counter()
    for _ in range(iterations):
        buffer = bytes(buffer_size)
        _ = buffer[0]  # Touch the buffer to ensure allocation
    non_pooled_time = time.perf_counter() - start_time
    print(f"  Time for {iterations} allocations: {non_pooled_time:.3f}s")
    print(f"  Average per allocation: {non_pooled_time / iterations * 1000:.2f}ms")

    # Pooled allocation timing
    print("\nPooled allocation:")
    # Pre-populate pool
    for _ in range(BufferPool.MAX_POOL_SIZE):
        BufferPool.return_bytes_buffer(bytes(buffer_size))

    start_time = time.perf_counter()
    for _ in range(iterations):
        buffer = BufferPool.get_bytes_buffer(buffer_size)
        _ = buffer[0]  # Touch the buffer
        BufferPool.return_bytes_buffer(buffer)
    pooled_time = time.perf_counter() - start_time
    print(f"  Time for {iterations} allocations: {pooled_time:.3f}s")
    print(f"  Average per allocation: {pooled_time / iterations * 1000:.2f}ms")

    # Performance improvement
    speedup = non_pooled_time / pooled_time
    print(f"\nSpeedup: {speedup:.1f}x faster with pooling")

    # Array performance comparison
    print("\nArray allocation comparison:")
    shape = (1404, 1872)  # Full display size

    # Non-pooled numpy
    start_time = time.perf_counter()
    for _ in range(50):
        arr = np.empty(shape, dtype=np.uint8)
        arr.fill(0xFF)
    non_pooled_array_time = time.perf_counter() - start_time

    # Pooled numpy
    for _ in range(BufferPool.MAX_POOL_SIZE):
        BufferPool.return_array_buffer(np.empty(shape, dtype=np.uint8))

    start_time = time.perf_counter()
    for _ in range(50):
        arr = BufferPool.get_array_buffer(shape, dtype=np.uint8, fill_value=0xFF)
        BufferPool.return_array_buffer(arr)
    pooled_array_time = time.perf_counter() - start_time

    array_speedup = non_pooled_array_time / pooled_array_time
    print(f"  Array allocation speedup: {array_speedup:.1f}x")

    # Clean up
    BufferPool.clear_pools()


def demo_memory_monitoring() -> None:
    """Demonstrate memory usage monitoring with buffer pools."""
    print_section("Memory Usage Monitoring")

    # Clear any existing pools and garbage collect
    BufferPool.clear_pools()
    gc.collect()

    # Start memory tracing
    tracemalloc.start()

    # Get baseline memory
    baseline_current, _ = tracemalloc.get_traced_memory()
    print(f"Baseline memory: {baseline_current:,} bytes")

    # Allocate multiple large buffers without pooling
    print("\nAllocating 10 x 1MB buffers without pooling:")
    buffers = []
    for _ in range(10):
        buffers.append(bytes(1024 * 1024))

    no_pool_current, _ = tracemalloc.get_traced_memory()
    print(f"  Current memory: {no_pool_current:,} bytes")
    print(f"  Memory increase: {(no_pool_current - baseline_current):,} bytes")

    # Clear buffers
    buffers.clear()
    gc.collect()

    # Now use buffer pooling
    print("\nAllocating 10 x 1MB buffers WITH pooling:")
    for _ in range(10):
        with ManagedBuffer.bytes(1024 * 1024) as buffer:
            # Simulate some work
            _ = buffer[0]

    pooled_current, pooled_peak = tracemalloc.get_traced_memory()
    print(f"  Current memory: {pooled_current:,} bytes")
    print(f"  Peak memory: {pooled_peak:,} bytes")
    print(f"  Pool efficiency: Only {BufferPool.MAX_POOL_SIZE} buffers kept in memory")

    # Show pool state (would need public methods to access pool info)
    print("\nBuffer pool state:")
    print("  Multiple pools created for different sizes and types")

    # Clean up
    tracemalloc.stop()
    BufferPool.clear_pools()


def simulate_display_operation(display_id: int, iterations: int) -> None:
    """Simulate display operations using buffer pool."""
    for _ in range(iterations):
        # Simulate getting display buffer
        with ManagedBuffer.array((1404, 1872), dtype=np.uint8) as buffer:
            # Simulate image processing
            buffer.fill(0xFF)  # Clear to white

            # Simulate drawing operations
            buffer[100:200, 100:200] = 0x00  # Draw black square

            # Simulate partial update buffer
            with ManagedBuffer.bytes(100 * 100, fill_value=0x80) as partial:
                # Process partial update
                _ = partial[0]

        # Small delay to simulate display update
        time.sleep(0.001)

    print(f"Thread {display_id} completed {iterations} operations")


def demo_thread_safe_sharing() -> None:
    """Demonstrate thread-safe buffer sharing across multiple threads."""
    print_section("Thread-Safe Buffer Sharing")

    # Clear any existing pools
    BufferPool.clear_pools()

    # Number of threads and operations
    num_threads = 4
    operations_per_thread = 25

    print(f"Running {num_threads} threads, each performing {operations_per_thread} operations")
    print("Each operation allocates a full display buffer and a partial update buffer\n")

    # Use ThreadPoolExecutor for concurrent operations
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        start_time = time.perf_counter()

        # Submit tasks
        for i in range(num_threads):
            future = executor.submit(simulate_display_operation, i, operations_per_thread)
            futures.append(future)

        # Wait for completion
        for future in futures:
            future.result()

    elapsed_time = time.perf_counter() - start_time
    total_operations = num_threads * operations_per_thread

    print(f"\nCompleted {total_operations} operations in {elapsed_time:.2f}s")
    print(f"Operations per second: {total_operations / elapsed_time:.0f}")

    # Show final pool state
    print("\nFinal pool state:")
    print("  Multiple buffers pooled for reuse")

    # Clean up
    BufferPool.clear_pools()


def demo_epaper_use_cases() -> None:
    """Demonstrate real-world e-paper display use cases."""
    print_section("E-Paper Display Use Cases")

    # Clear any existing pools
    BufferPool.clear_pools()

    # 1. Display clearing operation
    print("1. Display Clearing:")
    display_size = 1872 * 1404  # 10.3" display

    with ManagedBuffer.bytes(display_size, fill_value=0xFF) as clear_buffer:
        print(f"   Allocated {len(clear_buffer):,} byte buffer for clearing")
        # In real usage, this would be sent to display

    # 2. Image format conversion (8-bit to 4-bit)
    print("\n2. Image Format Conversion (8bpp to 4bpp):")
    with ManagedBuffer.array((1404, 1872), dtype=np.uint8) as src_image:
        # Simulate loading an 8-bit image
        src_image.fill(128)  # Mid-gray

        with ManagedBuffer.array((1404, 936), dtype=np.uint8) as packed_image:
            # Pack two 4-bit pixels per byte
            print(f"   Source: {src_image.nbytes:,} bytes")
            print(f"   Packed: {packed_image.nbytes:,} bytes")
            print(f"   Compression: {src_image.nbytes / packed_image.nbytes:.1f}x")

    # 3. Partial update with alignment
    print("\n3. Partial Update with Alignment:")
    # E-paper often requires 4-pixel alignment
    update_width = 100
    update_height = 100
    aligned_width = (update_width + 3) & ~3  # Align to 4 pixels

    with ManagedBuffer.array((update_height, aligned_width), dtype=np.uint8) as update_buffer:
        print(f"   Original size: {update_width}x{update_height}")
        print(f"   Aligned size: {aligned_width}x{update_height}")
        print(f"   Buffer size: {update_buffer.nbytes:,} bytes")

    # 4. Multi-region update
    print("\n4. Multi-Region Update:")
    regions = [(100, 100, 200, 200), (300, 300, 400, 400), (500, 100, 600, 200)]

    for i, (x1, y1, x2, y2) in enumerate(regions):
        width = x2 - x1
        height = y2 - y1
        with ManagedBuffer.array((height, width), dtype=np.uint8, fill_value=0x00) as region:
            print(f"   Region {i + 1}: {width}x{height} = {region.nbytes:,} bytes")

    # 5. Progressive image loading
    print("\n5. Progressive Image Loading:")
    chunk_height = 100  # Load image in chunks to save memory
    total_chunks = 1404 // chunk_height

    print(f"   Loading {total_chunks} chunks of {chunk_height} rows each")
    for chunk in range(3):  # Demo first 3 chunks
        with ManagedBuffer.array((chunk_height, 1872), dtype=np.uint8) as chunk_buffer:
            print(f"   Chunk {chunk + 1}: {chunk_buffer.nbytes:,} bytes")

    # Show memory efficiency
    print("\nMemory efficiency:")
    print(f"  Without pooling: Would allocate {display_size + 1404 * 1872 + 3 * 10000:,} bytes")
    print(f"  With pooling: Max {BufferPool.MAX_POOL_SIZE} buffers per size in memory")

    # Clean up
    BufferPool.clear_pools()


def demo_best_practices() -> None:
    """Demonstrate best practices for buffer pool usage."""
    print_section("Buffer Pool Best Practices")

    print("1. Always use context managers for automatic cleanup:")
    print("   with ManagedBuffer.bytes(size) as buffer:")
    print("       # Use buffer")
    print("   # Automatically returned to pool")

    print("\n2. Clear pools when switching between different workloads:")
    print("   BufferPool.clear_pools()  # Free all pooled memory")

    print("\n3. Pre-populate pools for known sizes:")
    # Example: pre-populate for display operations
    display_size = 1872 * 1404
    for _ in range(BufferPool.MAX_POOL_SIZE):
        buffer = BufferPool.get_bytes_buffer(display_size)
        BufferPool.return_bytes_buffer(buffer)
    print(f"   Pre-populated pool with {BufferPool.MAX_POOL_SIZE} x {display_size:,} byte buffers")

    print("\n4. Use appropriate buffer types:")
    print("   - bytes: For raw binary data (SPI transfers)")
    print("   - numpy arrays: For image processing and manipulation")

    print("\n5. Consider pool size limits:")
    print(f"   - Current MAX_POOL_SIZE: {BufferPool.MAX_POOL_SIZE}")
    print("   - Adjust based on memory constraints and usage patterns")

    print("\n6. Thread safety is built-in:")
    print("   - Safe to use from multiple threads")
    print("   - No additional locking needed")

    print("\n7. Profile your specific use case:")
    print("   - Not all operations benefit from pooling")
    print("   - Small, frequent allocations benefit most")

    # Clean up
    BufferPool.clear_pools()


def main() -> None:
    """Run all buffer pool demonstrations."""
    print("IT8951 Buffer Pool Demonstration")
    print("================================")
    print("This demo shows how to use buffer pooling for efficient memory")
    print("management in e-paper display operations.")

    try:
        # Run all demonstrations
        demo_basic_bytes_buffer()
        demo_numpy_array_buffer()
        demo_managed_buffer_context()
        demo_performance_comparison()
        demo_memory_monitoring()
        demo_thread_safe_sharing()
        demo_epaper_use_cases()
        demo_best_practices()

        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Always clean up
        BufferPool.clear_pools()
        print("\nBuffer pools cleared")


if __name__ == "__main__":
    main()
