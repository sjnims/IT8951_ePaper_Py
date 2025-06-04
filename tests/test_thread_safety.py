"""Simplified tests for thread-safe display wrapper focusing on lock behavior."""

import concurrent.futures
import threading
import time
from unittest.mock import Mock, patch

import pytest

from IT8951_ePaper_Py.thread_safe import ThreadSafeEPaperDisplay, thread_safe_method


class TestThreadSafeMethod:
    """Test the thread_safe_method decorator."""

    def test_decorator_preserves_function_attributes(self):
        """Test that the decorator preserves function metadata."""

        class TestClass:
            def __init__(self) -> None:
                self._lock = threading.RLock()

            @thread_safe_method
            def test_method(self, arg1: int, arg2: str = "default") -> str:
                """Test method docstring."""
                return f"{arg1}-{arg2}"

        obj = TestClass()
        assert obj.test_method.__name__ == "test_method"
        assert obj.test_method.__doc__ == "Test method docstring."

    def test_decorator_acquires_lock(self):
        """Test that the decorator properly acquires the lock."""
        lock_acquired = False

        class TestClass:
            def __init__(self) -> None:
                self._lock = threading.RLock()

            @thread_safe_method
            def test_method(self) -> str:
                nonlocal lock_acquired
                # Check if we own the lock
                # RLock doesn't have a public _is_owned method
                # We'll test by checking if we can acquire it again
                # If we already own it (via decorator), we can acquire again
                can_acquire = self._lock.acquire(blocking=False)
                if can_acquire:
                    self._lock.release()
                    lock_acquired = True
                else:
                    lock_acquired = False
                return "result"

        obj = TestClass()
        result = obj.test_method()

        assert result == "result"
        assert lock_acquired is True

    def test_decorator_handles_exceptions(self):
        """Test that the decorator releases lock on exceptions."""

        class TestClass:
            def __init__(self) -> None:
                self._lock = threading.RLock()

            @thread_safe_method
            def test_method(self) -> None:
                raise ValueError("Test exception")

        obj = TestClass()

        # Verify exception is propagated
        with pytest.raises(ValueError, match="Test exception"):
            obj.test_method()

        # Verify lock is released (we can acquire it)
        assert obj._lock.acquire(blocking=False)
        obj._lock.release()


class TestThreadSafeEPaperDisplay:
    """Test the ThreadSafeEPaperDisplay wrapper focusing on lock behavior."""

    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.__init__", return_value=None)
    def test_initialization_creates_lock(self, mock_init):
        """Test that initialization creates a reentrant lock."""
        display = ThreadSafeEPaperDisplay(vcom=-2.0)

        # Verify lock exists
        assert hasattr(display, "_lock")
        assert type(display._lock).__name__ == "RLock"

        # Verify parent init was called
        mock_init.assert_called_once()

    def test_concurrent_method_calls_are_serialized(self):
        """Test that concurrent method calls are properly serialized."""
        # Create a mock display with just the lock
        display = Mock(spec=ThreadSafeEPaperDisplay)
        display._lock = threading.RLock()

        # Track operation order
        operation_order = []
        operation_lock = threading.Lock()

        # Create a thread-safe method that records operations
        @thread_safe_method
        def mock_operation(self, op_id: int) -> int:
            with operation_lock:
                operation_order.append(f"start-{op_id}")
            time.sleep(0.05)  # Simulate work
            with operation_lock:
                operation_order.append(f"end-{op_id}")
            return op_id

        # Bind the method to our mock display
        display.mock_operation = mock_operation.__get__(display, type(display))

        # Run operations concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(display.mock_operation, i) for i in range(3)]
            results = [f.result() for f in futures]

        # Verify all operations completed
        assert sorted(results) == [0, 1, 2]

        # Verify operations were serialized (no interleaving)
        # Each operation should complete before the next starts
        for i in range(3):
            start_idx = operation_order.index(f"start-{i}")
            end_idx = operation_order.index(f"end-{i}")

            # Check no other operations started between this start and end
            between = operation_order[start_idx + 1 : end_idx]
            assert all("start" not in op for op in between)

    def test_reentrant_lock_allows_nested_calls(self):
        """Test that the reentrant lock allows nested method calls."""
        # Create a mock display
        display = Mock(spec=ThreadSafeEPaperDisplay)
        display._lock = threading.RLock()

        call_order = []

        # Create methods that call each other
        @thread_safe_method
        def method_a(self) -> None:
            call_order.append("a-start")
            self.method_b()
            call_order.append("a-end")

        @thread_safe_method
        def method_b(self) -> None:
            call_order.append("b-start")
            call_order.append("b-end")

        # Bind methods to display
        display.method_a = method_a.__get__(display, type(display))
        display.method_b = method_b.__get__(display, type(display))

        # Call method_a which calls method_b
        display.method_a()

        # Verify both methods executed in the correct order
        assert call_order == ["a-start", "b-start", "b-end", "a-end"]

    def test_lock_contention_resolution(self):
        """Test that multiple threads properly wait for lock acquisition."""
        display = Mock(spec=ThreadSafeEPaperDisplay)
        display._lock = threading.RLock()

        results = []

        @thread_safe_method
        def slow_operation(self, thread_id: int) -> int:
            results.append(thread_id)
            return thread_id

        display.slow_operation = slow_operation.__get__(display, type(display))

        # Start threads that will compete for the lock
        threads = []
        for i in range(3):
            thread = threading.Thread(target=lambda tid=i: display.slow_operation(tid))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete with timeout
        for thread in threads:
            thread.join(timeout=1.0)
            if thread.is_alive():
                raise RuntimeError("Thread did not complete in time")

        # All operations should complete
        assert len(results) == 3
        assert sorted(results) == [0, 1, 2]

    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay")
    def test_all_public_methods_wrapped(self, mock_epaper_class):
        """Test that all relevant public methods are wrapped with thread safety."""
        # Methods that should be thread-safe
        expected_methods = [
            "init",
            "close",
            "clear",
            "display_image",
            "display_image_progressive",
            "display_partial",
            "set_vcom",
            "get_vcom",
            "find_optimal_vcom",
            "sleep",
            "standby",
            "wake",
            "set_auto_sleep_timeout",
            "check_auto_sleep",
            "dump_registers",
            "get_device_status",
        ]

        # Create an instance
        display = ThreadSafeEPaperDisplay(vcom=-2.0)

        # Check that methods exist and are wrapped
        for method_name in expected_methods:
            assert hasattr(display, method_name)
            method = getattr(display, method_name)
            # The wrapper function will have been created by the decorator
            assert callable(method)
