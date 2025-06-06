"""Tests for memory monitoring utilities."""

import tracemalloc
from unittest.mock import MagicMock, patch

import pytest

from IT8951_ePaper_Py.memory_monitor import (
    MemoryMonitor,
    MemorySnapshot,
    estimate_memory_usage,
    get_memory_stats,
    monitor_memory,
)


class TestMemorySnapshot:
    """Test MemorySnapshot dataclass."""

    def test_memory_snapshot_creation(self) -> None:
        """Test creating a memory snapshot."""
        snapshot = MemorySnapshot(
            rss_mb=100.5,
            vms_mb=200.3,
            current_mb=50.2,
            peak_mb=75.8,
            total_objects=1000,
        )

        assert snapshot.rss_mb == 100.5
        assert snapshot.vms_mb == 200.3
        assert snapshot.current_mb == 50.2
        assert snapshot.peak_mb == 75.8
        assert snapshot.total_objects == 1000

    def test_memory_snapshot_str(self) -> None:
        """Test string representation of memory snapshot."""
        snapshot = MemorySnapshot(
            rss_mb=100.5,
            vms_mb=200.3,
            current_mb=50.2,
            peak_mb=75.8,
            total_objects=1234,
        )

        result = str(snapshot)
        assert "RSS=100.5MB" in result
        assert "VMS=200.3MB" in result
        assert "Python=50.2MB" in result
        assert "peak=75.8MB" in result
        assert "Objects=1,234" in result


class TestMemoryMonitor:
    """Test MemoryMonitor class."""

    @pytest.fixture
    def mock_process(self) -> MagicMock:
        """Create mock process."""
        process = MagicMock()
        # Mock memory_info
        mem_info = MagicMock()
        mem_info.rss = 100 * 1024 * 1024  # 100 MB
        mem_info.vms = 200 * 1024 * 1024  # 200 MB
        process.memory_info.return_value = mem_info
        process.memory_percent.return_value = 5.5
        return process

    def test_init(self, mock_process: MagicMock) -> None:
        """Test MemoryMonitor initialization."""
        with patch("psutil.Process", return_value=mock_process):
            monitor = MemoryMonitor()
            assert monitor.process == mock_process
            assert monitor.snapshots == []
            assert monitor._tracemalloc_started is False

    def test_start_tracking_not_running(self) -> None:
        """Test starting memory tracking when not already running."""
        # Ensure tracemalloc is stopped
        if tracemalloc.is_tracing():
            tracemalloc.stop()

        with patch("psutil.Process"):
            monitor = MemoryMonitor()
            monitor.start_tracking()

            assert tracemalloc.is_tracing()
            assert monitor._tracemalloc_started is True

            # Clean up
            tracemalloc.stop()

    def test_start_tracking_already_running(self) -> None:
        """Test starting memory tracking when already running."""
        # Start tracemalloc
        tracemalloc.start()

        with patch("psutil.Process"):
            monitor = MemoryMonitor()
            monitor.start_tracking()

            assert tracemalloc.is_tracing()
            assert monitor._tracemalloc_started is False  # Not started by us

            # Clean up
            tracemalloc.stop()

    def test_stop_tracking(self) -> None:
        """Test stopping memory tracking."""
        with patch("psutil.Process"):
            monitor = MemoryMonitor()
            monitor.start_tracking()
            assert tracemalloc.is_tracing()

            monitor.stop_tracking()
            assert not tracemalloc.is_tracing()
            assert monitor._tracemalloc_started is False

    def test_stop_tracking_not_started_by_us(self) -> None:
        """Test stopping tracking when not started by monitor."""
        # Start tracemalloc externally
        tracemalloc.start()

        with patch("psutil.Process"):
            monitor = MemoryMonitor()
            monitor._tracemalloc_started = False

            monitor.stop_tracking()
            # Should still be running since we didn't start it
            assert tracemalloc.is_tracing()

            # Clean up
            tracemalloc.stop()

    def test_take_snapshot_with_tracemalloc(self, mock_process: MagicMock) -> None:
        """Test taking a snapshot with tracemalloc enabled."""
        with patch("psutil.Process", return_value=mock_process):
            monitor = MemoryMonitor()
            monitor.start_tracking()

            with (
                patch(
                    "tracemalloc.get_traced_memory",
                    return_value=(50 * 1024 * 1024, 75 * 1024 * 1024),
                ),
                patch("gc.get_objects", return_value=[1] * 1000),
            ):
                snapshot = monitor.take_snapshot("Test")

            assert snapshot.rss_mb == 100.0
            assert snapshot.vms_mb == 200.0
            assert snapshot.current_mb == 50.0
            assert snapshot.peak_mb == 75.0
            assert snapshot.total_objects == 1000

            assert len(monitor.snapshots) == 1
            assert monitor.snapshots[0] == ("Test", snapshot)

            # Clean up
            monitor.stop_tracking()

    def test_take_snapshot_without_tracemalloc(self, mock_process: MagicMock) -> None:
        """Test taking a snapshot without tracemalloc enabled."""
        with patch("psutil.Process", return_value=mock_process):
            monitor = MemoryMonitor()

            with patch("gc.get_objects", return_value=[1] * 500):
                snapshot = monitor.take_snapshot("Test")

            assert snapshot.rss_mb == 100.0
            assert snapshot.vms_mb == 200.0
            assert snapshot.current_mb == 0.0  # No tracemalloc
            assert snapshot.peak_mb == 0.0  # No tracemalloc
            assert snapshot.total_objects == 500

    def test_get_memory_usage(self, mock_process: MagicMock) -> None:
        """Test getting current memory usage."""
        with patch("psutil.Process", return_value=mock_process):
            monitor = MemoryMonitor()
            usage = monitor.get_memory_usage()

            assert usage["rss_mb"] == 100.0
            assert usage["vms_mb"] == 200.0
            assert usage["percent"] == 5.5

    def test_print_summary_no_snapshots(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test printing summary with no snapshots."""
        with patch("psutil.Process"):
            monitor = MemoryMonitor()
            monitor.print_summary()

            captured = capsys.readouterr()
            assert "No memory snapshots taken" in captured.out

    def test_print_summary_single_snapshot(
        self, mock_process: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test printing summary with single snapshot."""
        with patch("psutil.Process", return_value=mock_process):
            monitor = MemoryMonitor()

            with patch("gc.get_objects", return_value=[1] * 100):
                monitor.take_snapshot("Test Snapshot")

            monitor.print_summary()

            captured = capsys.readouterr()
            assert "Memory Usage Summary:" in captured.out
            assert "Test Snapshot" in captured.out
            assert "RSS=100.0MB" in captured.out

    def test_print_summary_multiple_snapshots(
        self, mock_process: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test printing summary with multiple snapshots."""
        with patch("psutil.Process", return_value=mock_process):
            monitor = MemoryMonitor()
            monitor.start_tracking()

            # First snapshot
            with (
                patch(
                    "tracemalloc.get_traced_memory",
                    return_value=(50 * 1024 * 1024, 50 * 1024 * 1024),
                ),
                patch("gc.get_objects", return_value=[1] * 100),
            ):
                monitor.take_snapshot("Start")

            # Modify mock for second snapshot
            mock_process.memory_info.return_value.rss = 150 * 1024 * 1024  # 150 MB

            # Second snapshot
            with (
                patch(
                    "tracemalloc.get_traced_memory",
                    return_value=(80 * 1024 * 1024, 80 * 1024 * 1024),
                ),
                patch("gc.get_objects", return_value=[1] * 200),
            ):
                monitor.take_snapshot("End")

            monitor.print_summary()

            captured = capsys.readouterr()
            assert "Memory Changes:" in captured.out
            assert "RSS: +50.0MB" in captured.out
            assert "Python: +30.0MB" in captured.out
            assert "Objects: +100" in captured.out

            # Clean up
            monitor.stop_tracking()

    def test_get_top_allocations_no_tracemalloc(self) -> None:
        """Test getting top allocations without tracemalloc."""
        if tracemalloc.is_tracing():
            tracemalloc.stop()

        with patch("psutil.Process"):
            monitor = MemoryMonitor()
            result = monitor.get_top_allocations()

            assert len(result) == 1
            assert result[0] == "Tracemalloc not running"

    def test_get_top_allocations_with_tracemalloc(self) -> None:
        """Test getting top allocations with tracemalloc."""
        tracemalloc.start()

        # Create some allocations
        data1 = [0] * 1000
        data2 = [1] * 2000
        data3 = [2] * 3000

        with patch("psutil.Process"):
            monitor = MemoryMonitor()
            result = monitor.get_top_allocations(limit=5)

            assert isinstance(result, list)
            assert len(result) <= 5
            for line in result:
                assert line.startswith("#")
                assert "MB" in line

        # Clean up
        del data1, data2, data3
        tracemalloc.stop()

    def test_get_top_allocations_empty_formatted(self) -> None:
        """Test getting top allocations with empty formatted traceback."""
        tracemalloc.start()

        with patch("psutil.Process"):
            monitor = MemoryMonitor()

            # Mock the snapshot to return a stat with empty formatted traceback
            mock_snapshot = MagicMock()
            mock_stat = MagicMock()
            mock_stat.size = 1024 * 1024  # 1 MB
            mock_stat.traceback.format.return_value = []  # Empty formatted list
            mock_snapshot.statistics.return_value = [mock_stat]

            with patch("tracemalloc.take_snapshot", return_value=mock_snapshot):
                result = monitor.get_top_allocations(limit=1)

            assert len(result) == 1
            assert "#1: <unknown>: 1.0 MB" in result[0]

        tracemalloc.stop()


class TestContextManager:
    """Test monitor_memory context manager."""

    def test_monitor_memory_context(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test monitor_memory context manager."""
        with patch("psutil.Process") as mock_process_class:
            mock_process = MagicMock()
            mem_info = MagicMock()
            mem_info.rss = 100 * 1024 * 1024
            mem_info.vms = 200 * 1024 * 1024
            mock_process.memory_info.return_value = mem_info
            mock_process_class.return_value = mock_process

            with monitor_memory("Test Operation") as monitor:
                assert isinstance(monitor, MemoryMonitor)
                assert len(monitor.snapshots) == 1  # Initial snapshot

                # Take additional snapshot
                monitor.take_snapshot("During operation")

            # After exiting, should have printed summary
            captured = capsys.readouterr()
            assert "Memory Usage Summary:" in captured.out
            assert "Test Operation - Start" in captured.out
            assert "Test Operation - End" in captured.out
            assert len(monitor.snapshots) == 3  # Start, During, End

    def test_monitor_memory_with_exception(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test monitor_memory handles exceptions properly."""
        with patch("psutil.Process") as mock_process_class:
            mock_process = MagicMock()
            mem_info = MagicMock()
            mem_info.rss = 100 * 1024 * 1024
            mem_info.vms = 200 * 1024 * 1024
            mock_process.memory_info.return_value = mem_info
            mock_process_class.return_value = mock_process

            try:
                with monitor_memory("Error Test") as monitor:
                    assert isinstance(monitor, MemoryMonitor)
                    raise ValueError("Test error")
            except ValueError:
                pass

            # Should still print summary even with exception
            captured = capsys.readouterr()
            assert "Memory Usage Summary:" in captured.out


class TestUtilityFunctions:
    """Test utility functions."""

    def test_estimate_memory_usage_basic(self) -> None:
        """Test basic memory estimation."""
        result = estimate_memory_usage(1000, 1000, 2)  # 1000x1000, 4bpp

        assert result["input_size_mb"] == pytest.approx(0.953674, rel=1e-3)
        assert result["packed_size_mb"] == pytest.approx(0.476837, rel=1e-3)
        assert result["compression_ratio"] == pytest.approx(2.0)

    def test_estimate_memory_usage_all_formats(self) -> None:
        """Test memory estimation for all pixel formats."""
        width, height = 800, 600

        # Test each format
        formats = [
            (0, 0.125),  # 1bpp
            (1, 0.25),  # 2bpp
            (2, 0.5),  # 4bpp
            (3, 1.0),  # 8bpp
        ]

        for pixel_format, bytes_per_pixel in formats:
            result = estimate_memory_usage(width, height, pixel_format)

            input_size = (width * height) / (1024 * 1024)
            packed_size = (width * height * bytes_per_pixel) / (1024 * 1024)

            assert result["input_size_mb"] == pytest.approx(input_size)
            assert result["packed_size_mb"] == pytest.approx(packed_size)

    def test_estimate_memory_usage_with_buffer(self) -> None:
        """Test memory estimation with buffer overhead."""
        result = estimate_memory_usage(1000, 1000, 2, include_buffer=True)

        assert result["buffer_overhead_mb"] > 0
        assert result["total_mb"] > result["input_size_mb"] + result["packed_size_mb"]

    def test_estimate_memory_usage_without_buffer(self) -> None:
        """Test memory estimation without buffer overhead."""
        result = estimate_memory_usage(1000, 1000, 2, include_buffer=False)

        assert result["buffer_overhead_mb"] == 0
        assert result["total_mb"] == result["input_size_mb"] + result["packed_size_mb"]

    def test_estimate_memory_usage_zero_packed_size(self) -> None:
        """Test memory estimation with zero dimensions."""
        result = estimate_memory_usage(0, 0, 2)

        assert result["packed_size_mb"] == 0
        assert result["compression_ratio"] == 1.0

    def test_estimate_memory_usage_unknown_format(self) -> None:
        """Test memory estimation with unknown format."""
        result = estimate_memory_usage(1000, 1000, 99)  # Unknown format

        # Should use default 1.0 bytes per pixel
        assert result["compression_ratio"] == pytest.approx(1.0)

    def test_get_memory_stats(self) -> None:
        """Test getting comprehensive memory statistics."""
        with patch("psutil.Process") as mock_process_class:
            mock_process = MagicMock()
            mem_info = MagicMock()
            mem_info.rss = 100 * 1024 * 1024
            mem_info.vms = 200 * 1024 * 1024
            mock_process.memory_info.return_value = mem_info
            mock_process.memory_percent.return_value = 5.5
            mock_process_class.return_value = mock_process

            with patch("psutil.virtual_memory") as mock_virtual_memory:
                virtual_mem = MagicMock()
                virtual_mem.total = 8 * 1024 * 1024 * 1024  # 8 GB
                virtual_mem.available = 4 * 1024 * 1024 * 1024  # 4 GB
                virtual_mem.percent = 50.0
                mock_virtual_memory.return_value = virtual_mem

                with (
                    patch("gc.get_objects", return_value=[1] * 1000),
                    patch("gc.garbage", [1, 2, 3]),
                ):
                    stats = get_memory_stats()

        assert stats["process"]["rss_mb"] == 100.0
        assert stats["process"]["vms_mb"] == 200.0
        assert stats["process"]["percent"] == 5.5
        assert stats["system"]["total_mb"] == 8192.0
        assert stats["system"]["available_mb"] == 4096.0
        assert stats["system"]["percent"] == 50.0
        assert stats["python"]["objects"] == 1000
        assert stats["python"]["garbage"] == 3
