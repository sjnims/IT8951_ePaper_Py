"""Memory monitoring utilities for IT8951 e-paper driver.

This module provides tools for monitoring and profiling memory usage
during e-paper display operations to help optimize memory consumption.
"""

import gc
import tracemalloc
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import psutil


@dataclass
class MemorySnapshot:
    """Memory usage snapshot."""

    # Process memory (from psutil)
    rss_mb: float  # Resident Set Size in MB
    vms_mb: float  # Virtual Memory Size in MB

    # Python memory (from tracemalloc)
    current_mb: float  # Current allocated memory in MB
    peak_mb: float  # Peak allocated memory in MB

    # Object counts
    total_objects: int  # Total Python objects

    def __str__(self) -> str:
        """Format memory snapshot as string."""
        return (
            f"Memory: RSS={self.rss_mb:.1f}MB, VMS={self.vms_mb:.1f}MB, "
            f"Python={self.current_mb:.1f}MB (peak={self.peak_mb:.1f}MB), "
            f"Objects={self.total_objects:,}"
        )


class MemoryMonitor:
    """Monitor memory usage during operations."""

    def __init__(self) -> None:
        """Initialize memory monitor."""
        self.process = psutil.Process()
        self.snapshots: list[tuple[str, MemorySnapshot]] = []
        self._tracemalloc_started = False

    def start_tracking(self) -> None:
        """Start memory tracking."""
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            self._tracemalloc_started = True

    def stop_tracking(self) -> None:
        """Stop memory tracking."""
        if self._tracemalloc_started and tracemalloc.is_tracing():
            tracemalloc.stop()
            self._tracemalloc_started = False

    def take_snapshot(self, label: str) -> MemorySnapshot:
        """Take a memory snapshot.

        Args:
            label: Label for this snapshot.

        Returns:
            MemorySnapshot with current memory usage.
        """
        # Force garbage collection for accurate measurements
        gc.collect()

        # Get process memory info
        mem_info = self.process.memory_info()
        rss_mb = mem_info.rss / 1024 / 1024
        vms_mb = mem_info.vms / 1024 / 1024

        # Get Python memory info
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            current_mb = current / 1024 / 1024
            peak_mb = peak / 1024 / 1024
        else:
            current_mb = peak_mb = 0.0

        # Count objects
        total_objects = len(gc.get_objects())

        snapshot = MemorySnapshot(
            rss_mb=rss_mb,
            vms_mb=vms_mb,
            current_mb=current_mb,
            peak_mb=peak_mb,
            total_objects=total_objects,
        )

        self.snapshots.append((label, snapshot))
        return snapshot

    def get_memory_usage(self) -> dict[str, float]:
        """Get current memory usage.

        Returns:
            Dictionary with memory usage in MB.
        """
        mem_info = self.process.memory_info()
        return {
            "rss_mb": mem_info.rss / 1024 / 1024,
            "vms_mb": mem_info.vms / 1024 / 1024,
            "percent": self.process.memory_percent(),
        }

    def print_summary(self) -> None:
        """Print memory usage summary."""
        if not self.snapshots:
            print("No memory snapshots taken")
            return

        print("\nMemory Usage Summary:")
        print("-" * 80)

        for label, snapshot in self.snapshots:
            print(f"{label:30} {snapshot}")

        # Calculate deltas if we have multiple snapshots
        if len(self.snapshots) > 1:
            print("\nMemory Changes:")
            print("-" * 80)

            first_label, first = self.snapshots[0]
            for label, snapshot in self.snapshots[1:]:
                rss_delta = snapshot.rss_mb - first.rss_mb
                python_delta = snapshot.current_mb - first.current_mb
                obj_delta = snapshot.total_objects - first.total_objects

                print(
                    f"{first_label} -> {label:20} "
                    f"RSS: {rss_delta:+.1f}MB, "
                    f"Python: {python_delta:+.1f}MB, "
                    f"Objects: {obj_delta:+,}"
                )

    def get_top_allocations(self, limit: int = 10) -> list[str]:
        """Get top memory allocations.

        Args:
            limit: Number of top allocations to return.

        Returns:
            List of formatted allocation strings.
        """
        if not tracemalloc.is_tracing():
            return ["Tracemalloc not running"]

        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")

        lines: list[str] = []
        for index, stat in enumerate(top_stats[:limit], 1):
            size_mb = stat.size / 1024 / 1024
            # Format the traceback to get filename and line number
            formatted = stat.traceback.format()
            if formatted:
                # Extract filename and line from formatted string
                # Format: '  File "path/file.py", line 123'
                line_info = formatted[0].strip()
                lines.append(f"#{index}: {line_info}: {size_mb:.1f} MB")
            else:
                lines.append(f"#{index}: <unknown>: {size_mb:.1f} MB")

        return lines


@contextmanager
def monitor_memory(label: str = "Operation") -> Generator[MemoryMonitor, None, None]:
    """Context manager for monitoring memory usage.

    Usage:
        with monitor_memory("Image processing") as monitor:
            # Do memory-intensive operations
            process_image()
            monitor.take_snapshot("After processing")

        # Prints summary automatically on exit

    Args:
        label: Label for the operation being monitored.

    Yields:
        MemoryMonitor instance.
    """
    monitor = MemoryMonitor()
    monitor.start_tracking()

    # Take initial snapshot
    monitor.take_snapshot(f"{label} - Start")

    try:
        yield monitor
    finally:
        # Take final snapshot
        monitor.take_snapshot(f"{label} - End")

        # Print summary
        monitor.print_summary()

        # Stop tracking
        monitor.stop_tracking()


def estimate_memory_usage(
    width: int, height: int, pixel_format: int, include_buffer: bool = True
) -> dict[str, float]:
    """Estimate memory usage for display operations.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        pixel_format: Pixel format (0=1bpp, 1=2bpp, 2=4bpp, 3=8bpp).
        include_buffer: Include buffer overhead in estimation.

    Returns:
        Dictionary with memory estimates in MB.
    """
    total_pixels = width * height

    # Bytes per pixel for each format
    bytes_per_pixel = {
        0: 0.125,  # 1bpp = 1/8 byte per pixel
        1: 0.25,  # 2bpp = 1/4 byte per pixel
        2: 0.5,  # 4bpp = 1/2 byte per pixel
        3: 1.0,  # 8bpp = 1 byte per pixel
    }

    bpp = bytes_per_pixel.get(pixel_format, 1.0)

    # Calculate sizes
    input_size_mb = total_pixels / 1024 / 1024  # Input is always 8bpp
    packed_size_mb = (total_pixels * bpp) / 1024 / 1024

    # Buffer overhead (alignment, temporary buffers)
    buffer_overhead_mb = 0.0
    if include_buffer:
        # Assume 10% overhead for alignment and temporary buffers
        buffer_overhead_mb = (input_size_mb + packed_size_mb) * 0.1

    total_mb = input_size_mb + packed_size_mb + buffer_overhead_mb

    return {
        "input_size_mb": input_size_mb,
        "packed_size_mb": packed_size_mb,
        "buffer_overhead_mb": buffer_overhead_mb,
        "total_mb": total_mb,
        "compression_ratio": input_size_mb / packed_size_mb if packed_size_mb > 0 else 1.0,
    }


def get_memory_stats() -> dict[str, Any]:
    """Get comprehensive memory statistics.

    Returns:
        Dictionary with system and process memory stats.
    """
    process = psutil.Process()
    mem_info = process.memory_info()
    virtual_mem = psutil.virtual_memory()

    return {
        "process": {
            "rss_mb": mem_info.rss / 1024 / 1024,
            "vms_mb": mem_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
        },
        "system": {
            "total_mb": virtual_mem.total / 1024 / 1024,
            "available_mb": virtual_mem.available / 1024 / 1024,
            "percent": virtual_mem.percent,
        },
        "python": {
            "objects": len(gc.get_objects()),
            "garbage": len(gc.garbage),
        },
    }
