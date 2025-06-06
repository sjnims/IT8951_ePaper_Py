#!/usr/bin/env python3
"""Integration scenarios demonstrating complex workflows with the IT8951 e-paper display.

This example shows how to combine multiple features of the library:
- Power management with display operations
- Progressive loading with bit depth optimization
- Error recovery with retry mechanisms
- Memory management with buffer pools
- Thread safety in concurrent operations
"""

import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.buffer_pool import BufferPool
from IT8951_ePaper_Py.constants import DisplayMode, PixelFormat
from IT8951_ePaper_Py.debug_mode import DebugLevel
from IT8951_ePaper_Py.exceptions import IT8951Error
from IT8951_ePaper_Py.memory_monitor import MemoryMonitor
from IT8951_ePaper_Py.retry_policy import RetryPolicy
from IT8951_ePaper_Py.retry_policy import with_retry as retry
from IT8951_ePaper_Py.thread_safe import ThreadSafeEPaperDisplay


def np_to_pil(array: NDArray[np.generic]) -> Image.Image:
    """Convert numpy array to PIL Image."""
    # Ensure the array is uint8
    if hasattr(array, "dtype") and array.dtype != np.uint8:
        array = array.astype(np.uint8)
    return Image.fromarray(array, mode="L")


def scenario_1_power_aware_multi_update(display: EPaperDisplay) -> None:
    """Scenario 1: Power-aware multi-update workflow.

    Demonstrates:
    - Auto-sleep after inactivity
    - Wake on demand
    - Multiple display mode updates
    - Power state monitoring
    """
    print("\n=== Scenario 1: Power-Aware Multi-Update ===")

    # Set aggressive auto-sleep for demo
    display.set_auto_sleep_timeout(5.0)
    print("Auto-sleep timeout set to 5 seconds")

    # Create test images
    width, height = display.width, display.height
    images = {
        "full": np.ones((height, width), dtype=np.uint8) * 255,  # White
        "partial": np.zeros((200, 200), dtype=np.uint8),  # Black square
        "gradient": np.linspace(0, 255, width * height, dtype=np.uint8).reshape(height, width),
    }

    # Initial full update
    print("\n1. Full screen update (INIT mode)")
    display.display_image(np_to_pil(images["full"]), mode=DisplayMode.INIT)
    print(f"Power state: {display.get_device_status()['power_state']}")

    # Wait for auto-sleep
    print("\n2. Waiting 6 seconds for auto-sleep...")
    time.sleep(6)
    print(f"Power state: {display.get_device_status()['power_state']}")

    # Partial update (should auto-wake)
    print("\n3. Partial update at (100, 100) - should auto-wake")
    display.display_image(np_to_pil(images["partial"]), x=100, y=100, mode=DisplayMode.DU)
    print(f"Power state: {display.get_device_status()['power_state']}")

    # Fast animation with A2 mode
    print("\n4. Fast animation with A2 mode (5 frames)")
    for _ in range(5):
        frame = np.random.randint(0, 2, size=(100, 100), dtype=np.uint8) * 255
        display.display_image(np_to_pil(frame), x=300, y=300, mode=DisplayMode.A2)
        time.sleep(0.1)

    # A2 counter is internal - just note that it tracks usage
    print("Note: A2 mode usage is tracked internally for auto-clearing")

    # Final update with gradient
    print("\n5. Gradient update with GC16 mode")
    display.display_image(np_to_pil(images["gradient"]), mode=DisplayMode.GC16)

    print("\nScenario 1 complete!")


def scenario_2_progressive_loading_optimization(display: EPaperDisplay) -> None:
    """Scenario 2: Progressive loading with bit depth optimization.

    Demonstrates:
    - Large image handling with progressive loading
    - Automatic bit depth selection
    - Memory monitoring
    - Performance optimization
    """
    print("\n=== Scenario 2: Progressive Loading & Optimization ===")

    # Enable memory monitoring
    monitor = MemoryMonitor()
    monitor.start_tracking()

    # Create large test image
    width, height = display.width, display.height

    print("\n1. Creating large grayscale image")
    # Simulate a complex grayscale pattern
    x = np.linspace(0, 4 * np.pi, width)
    y = np.linspace(0, 4 * np.pi, height)
    x_grid, y_grid = np.meshgrid(x, y)
    large_image = ((np.sin(x_grid) + np.cos(y_grid)) * 127.5 + 127.5).astype(np.uint8)

    memory_before = monitor.get_memory_usage()["python_current_mb"]
    print(f"Memory before: {memory_before:.2f} MB")

    # Test different bit depths
    bit_depths = [
        (PixelFormat.BPP_1, "1bpp (binary)"),
        (PixelFormat.BPP_2, "2bpp (4 levels)"),
        (PixelFormat.BPP_4, "4bpp (16 levels)"),
        (PixelFormat.BPP_8, "8bpp (256 levels)"),
    ]

    for pixel_format, description in bit_depths:
        print(f"\n2. Testing {description}")

        # Quantize image for lower bit depths
        if pixel_format == PixelFormat.BPP_1:
            test_image = (large_image > 128).astype(np.uint8) * 255
        elif pixel_format == PixelFormat.BPP_2:
            test_image = (large_image // 64) * 85  # 4 levels: 0, 85, 170, 255
        elif pixel_format == PixelFormat.BPP_4:
            test_image = (large_image // 16) * 17  # 16 levels
        else:
            test_image = large_image

        # Display with progressive loading if needed
        start_time = time.time()
        try:
            display.display_image(
                np_to_pil(test_image), pixel_format=pixel_format, mode=DisplayMode.GC16
            )
            elapsed = time.time() - start_time

            current_memory = monitor.get_memory_usage()["python_peak_mb"]
            memory_usage = current_memory - memory_before
            print(f"   - Time: {elapsed:.2f}s")
            print(f"   - Peak memory: +{memory_usage:.2f} MB")

        except IT8951Error as e:
            print(f"   - Error: {e}")

        # Reset tracking for next iteration
        monitor.stop_tracking()
        monitor.start_tracking()
        time.sleep(1)

    # Test progressive loading with very large image
    print("\n3. Testing progressive loading with oversized image")
    oversized = np.random.randint(0, 256, size=(3000, 3000), dtype=np.uint8)

    try:
        start_time = time.time()
        # This should trigger progressive loading
        display.display_image(np_to_pil(oversized), x=0, y=0, mode=DisplayMode.GC16)
        print(f"   - Progressive loading completed in {time.time() - start_time:.2f}s")
    except IT8951Error as e:
        print(f"   - Expected error for oversized image: {e}")

    monitor.stop_tracking()
    print("\nScenario 2 complete!")


def scenario_3_error_recovery_retry(display: EPaperDisplay) -> None:
    """Scenario 3: Error recovery with retry mechanisms.

    Demonstrates:
    - Custom retry policies
    - Error handling and recovery
    - Degraded mode operation
    - Diagnostic information
    """
    print("\n=== Scenario 3: Error Recovery & Retry ===")

    # Create custom retry policy
    aggressive_retry = RetryPolicy(max_attempts=5, delay=0.1, max_delay=2.0, backoff_factor=2.0)

    print("\n1. Testing retry with simulated failures")

    # Create a function that fails intermittently
    failure_count = 0

    @retry(aggressive_retry)
    def flaky_operation() -> str:
        nonlocal failure_count
        failure_count += 1
        if failure_count < 3:
            print(f"   Attempt {failure_count}: Simulated failure")
            raise IT8951Error("Simulated SPI communication error")
        print(f"   Attempt {failure_count}: Success!")
        return "Operation completed"

    try:
        result = flaky_operation()
        print(f"   Result: {result}")
    except IT8951Error as e:
        print(f"   Failed after all retries: {e}")

    # Test display operation with retry
    print("\n2. Testing display update with retry policy")
    test_image = np.ones((200, 200), dtype=np.uint8) * 128

    # Wrap display method with retry
    @retry(aggressive_retry)
    def reliable_display() -> None:
        display.display_image(np_to_pil(test_image), x=100, y=100, mode=DisplayMode.DU)

    try:
        reliable_display()
        print("   Display update successful")
    except IT8951Error as e:
        print(f"   Display update failed: {e}")

    # Test degraded mode operation
    print("\n3. Testing degraded mode with fallback")

    # Try high-quality mode first, fall back to faster mode
    modes_to_try = [
        (DisplayMode.GC16, "High quality (GC16)"),
        (DisplayMode.GL16, "Medium quality (GL16)"),
        (DisplayMode.DU, "Fast update (DU)"),
    ]

    test_pattern = np.random.randint(0, 256, size=(300, 300), dtype=np.uint8)

    for mode, description in modes_to_try:
        try:
            print(f"   Trying {description}...")
            display.display_image(np_to_pil(test_pattern), x=200, y=200, mode=mode)
            print(f"   Success with {description}")
            break
        except IT8951Error as e:
            print(f"   Failed: {e}")
            if mode == modes_to_try[-1][0]:
                print("   All modes failed!")

    print("\nScenario 3 complete!")


def scenario_4_concurrent_buffer_management(display: ThreadSafeEPaperDisplay) -> None:
    """Scenario 4: Thread-safe operations with buffer management.

    Demonstrates:
    - Thread-safe display wrapper
    - Buffer pool usage
    - Concurrent operations
    - Resource management
    """
    print("\n=== Scenario 4: Concurrent Buffer Management ===")

    # Note: BufferPool is a static pool implementation
    print("\n1. Using BufferPool for efficient memory reuse")
    print("   BufferPool manages memory automatically with thread safety")

    # Simulate concurrent operations
    import threading

    def worker(worker_id: int, num_operations: int) -> None:
        """Worker thread that performs display operations."""
        for i in range(num_operations):
            # Create small test image
            size = 100
            test_data = np.full((size, size), worker_id * 50 + i * 10, dtype=np.uint8)

            # Use BufferPool for array allocation
            buffer = BufferPool.get_array_buffer((size, size), dtype=np.uint8)
            buffer[:] = test_data

            # Display update (thread-safe)
            x = (worker_id * 150) % (display.width - size)
            y = (i * 100) % (display.height - size)

            try:
                display.display_image(np_to_pil(test_data), x=x, y=y, mode=DisplayMode.DU)
                print(f"   Worker {worker_id}: Updated region ({x}, {y})")
            except IT8951Error as e:
                print(f"   Worker {worker_id}: Error - {e}")
            finally:
                # Return buffer to pool
                BufferPool.return_array_buffer(buffer)

            time.sleep(0.1)  # Simulate processing time

    print("\n2. Starting 3 concurrent workers")
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker, args=(i, 3))
        threads.append(thread)
        thread.start()

    # Wait for completion
    for thread in threads:
        thread.join()

    print("\n3. Buffer pool benefits:")
    print("   - Automatic memory reuse reduces allocations")
    print("   - Thread-safe operations with internal locking")
    print("   - Reduced garbage collection pressure")

    print("\nScenario 4 complete!")


def scenario_5_advanced_debugging(display: EPaperDisplay) -> None:
    """Scenario 5: Advanced debugging and diagnostics.

    Demonstrates:
    - Debug mode with different levels
    - Performance profiling
    - Diagnostic information
    - Error context
    """
    print("\n=== Scenario 5: Advanced Debugging ===")

    # Test different debug levels
    debug_levels = [
        (DebugLevel.ERROR, "ERROR only"),
        (DebugLevel.INFO, "INFO level"),
        (DebugLevel.TRACE, "TRACE level (verbose)"),
    ]

    test_image = np.random.randint(0, 256, size=(200, 200), dtype=np.uint8)

    for level, description in debug_levels:
        print(f"\n1. Testing {description}")

        # Set debug level
        from IT8951_ePaper_Py.debug_mode import disable_debug, enable_debug

        enable_debug(level)
        try:
            # This will show debug output based on level
            display.display_image(
                np_to_pil(test_image),
                x=100,
                y=100,
                mode=DisplayMode.DU,
                pixel_format=PixelFormat.BPP_4,
            )
        except IT8951Error:
            pass  # Expected for demo
        finally:
            disable_debug()

        time.sleep(0.5)

    # Performance profiling
    print("\n2. Performance profiling")
    from IT8951_ePaper_Py.utils import timed_operation

    @timed_operation("profile_operation")
    def profile_operation() -> dict[str, Any]:
        """Profile different operations."""
        results = {}

        # Profile pixel packing
        for pixel_format in [PixelFormat.BPP_1, PixelFormat.BPP_2, PixelFormat.BPP_4]:
            data = np.random.randint(0, 256, size=(1000, 1000), dtype=np.uint8)

            start = time.time()
            # Pack pixels through display's method
            # Note: Direct controller access is internal
            # Just time the image conversion for demonstration
            _ = np_to_pil(data)
            results[f"pack_{pixel_format.value}bpp"] = time.time() - start

        return results

    results = profile_operation()
    print("   Pixel packing times:")
    for operation, duration in results.items():
        if isinstance(duration, float):
            print(f"   - {operation}: {duration * 1000:.2f} ms")

    # Diagnostic dump
    print("\n3. System diagnostics")
    status = display.get_device_status()
    print(f"   Power state: {status['power_state']}")
    print(f"   VCOM voltage: {status['vcom_voltage']}V")
    print(f"   A2 refresh count: {status['a2_refresh_count']}/{status['a2_refresh_limit']}")
    print(f"   Enhanced driving: {status['enhanced_driving']}")

    # Memory diagnostics
    print("\n4. Memory diagnostics")
    monitor = MemoryMonitor()
    monitor.start_tracking()

    # Simulate memory-intensive operation
    large_data = np.zeros((display.height, display.width), dtype=np.uint8)
    memory_before = monitor.get_memory_usage()["python_current_mb"]

    display.display_image(np_to_pil(large_data), mode=DisplayMode.INIT)

    memory_stats = monitor.get_memory_usage()
    memory_after = memory_stats["python_current_mb"]
    peak = memory_stats["python_peak_mb"]

    print(f"   Memory before: {memory_before:.2f} MB")
    print(f"   Memory after: {memory_after:.2f} MB")
    print(f"   Peak memory: {peak:.2f} MB")
    print(f"   Delta: {(memory_after - memory_before):.2f} MB")

    monitor.stop_tracking()

    print("\nScenario 5 complete!")


def main() -> None:
    """Run all integration scenarios."""
    if len(sys.argv) < 2:
        print("Usage: python integration_scenarios.py <vcom_voltage> [scenario]")
        print("Example: python integration_scenarios.py -1.45")
        print("         python integration_scenarios.py -1.45 2")
        print("\nScenarios:")
        print("  1 - Power-aware multi-update workflow")
        print("  2 - Progressive loading with optimization")
        print("  3 - Error recovery and retry mechanisms")
        print("  4 - Concurrent operations with buffer management")
        print("  5 - Advanced debugging and diagnostics")
        print("  all - Run all scenarios (default)")
        print("\n⚠️  IMPORTANT: The VCOM voltage MUST match your display's specification!")
        sys.exit(1)

    vcom = float(sys.argv[1])
    scenario = sys.argv[2] if len(sys.argv) > 2 else "all"

    print(f"Initializing e-paper display with VCOM: {vcom}V...")

    # Use thread-safe wrapper for scenario 4
    display = ThreadSafeEPaperDisplay(vcom=vcom) if scenario == "4" else EPaperDisplay(vcom=vcom)

    try:
        width, height = display.init()
        print(f"Display initialized: {width}x{height}")

        scenarios: dict[str, Callable[[Any], None]] = {
            "1": scenario_1_power_aware_multi_update,
            "2": scenario_2_progressive_loading_optimization,
            "3": scenario_3_error_recovery_retry,
            "4": scenario_4_concurrent_buffer_management,
            "5": scenario_5_advanced_debugging,
        }

        if scenario == "all":
            for num, func in scenarios.items():
                if num == "4":
                    # Switch to thread-safe display for scenario 4
                    thread_safe_display = ThreadSafeEPaperDisplay(vcom=vcom)
                    thread_safe_display.init()
                    func(thread_safe_display)
                else:
                    func(display)
                time.sleep(2)  # Pause between scenarios
        elif scenario in scenarios:
            scenarios[scenario](display)
        else:
            print(f"Unknown scenario: {scenario}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        display.clear()
        print("\nAll integration scenarios completed!")


if __name__ == "__main__":
    main()
