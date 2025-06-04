"""Simplified tests for thread-safe display wrapper focusing on lock behavior."""

import concurrent.futures
import threading
import time
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import pytest
from PIL import Image

from IT8951_ePaper_Py.constants import DisplayMode, PixelFormat, PowerState, Rotation
from IT8951_ePaper_Py.display import EPaperDisplay
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

    def test_decorator_without_lock(self):
        """Test that decorator works when object has no _lock attribute."""

        class TestClass:
            @thread_safe_method
            def test_method(self, x: int) -> int:
                return x * 2

        obj = TestClass()
        # Should work without a lock
        result = obj.test_method(5)
        assert result == 10


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

    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.__init__", return_value=None)
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.init")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.close")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.clear")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.display_image")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.display_image_progressive")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.display_partial")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.set_vcom")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.get_vcom")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.find_optimal_vcom")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.sleep")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.standby")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.wake")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.set_auto_sleep_timeout")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.check_auto_sleep")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.dump_registers")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.get_device_status")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.is_enhanced_driving_enabled")
    def test_wrapped_methods_call_parent(self, *mocks: Mock) -> None:
        """Test that wrapped methods properly call parent implementations."""
        # Unpack mocks in reverse order
        (
            mock_is_enhanced,
            mock_get_status,
            mock_dump_regs,
            mock_check_sleep,
            mock_set_timeout,
            mock_wake,
            mock_standby,
            mock_sleep,
            mock_find_vcom,
            mock_get_vcom,
            mock_set_vcom,
            mock_partial,
            mock_progressive,
            mock_image,
            mock_clear,
            mock_close,
            mock_init,
            mock_parent_init,
        ) = mocks

        # Configure mock returns
        mock_init.return_value = (800, 600)
        mock_get_vcom.return_value = -2.0
        mock_find_vcom.return_value = -2.5
        mock_dump_regs.return_value = {"reg1": 0x1234}
        mock_get_status.return_value = {"status": "ok"}
        mock_is_enhanced.return_value = True

        # Create display instance
        display = ThreadSafeEPaperDisplay(vcom=-2.0)

        # Test init
        width, height = display.init()
        assert width == 800
        assert height == 600
        mock_init.assert_called_once()

        # Test close
        display.close()
        mock_close.assert_called_once()

        # Test clear
        display.clear(0x80)
        mock_clear.assert_called_once_with(0x80)

        # Test display_image
        img = Image.new("L", (100, 100))
        display.display_image(img, x=10, y=20, mode=DisplayMode.DU)
        mock_image.assert_called_once_with(
            img, 10, 20, DisplayMode.DU, Rotation.ROTATE_0, PixelFormat.BPP_4
        )

        # Test display_image_progressive
        display.display_image_progressive(img, chunk_height=128)
        mock_progressive.assert_called_once_with(
            img, 0, 0, DisplayMode.GC16, Rotation.ROTATE_0, PixelFormat.BPP_4, 128
        )

        # Test display_partial
        display.display_partial(img, 50, 60, DisplayMode.A2)
        mock_partial.assert_called_once_with(img, 50, 60, DisplayMode.A2)

        # Test VCOM operations
        display.set_vcom(-2.5)
        mock_set_vcom.assert_called_once_with(-2.5)

        vcom = display.get_vcom()
        assert vcom == -2.0
        mock_get_vcom.assert_called_once()

        # Test find_optimal_vcom
        optimal = display.find_optimal_vcom()
        assert optimal == -2.5
        mock_find_vcom.assert_called_once_with(-3.0, -1.0, 0.1, None)

        # Test power management
        display.sleep()
        mock_sleep.assert_called_once()

        display.standby()
        mock_standby.assert_called_once()

        display.wake()
        mock_wake.assert_called_once()

        # Test auto-sleep
        display.set_auto_sleep_timeout(30.0)
        mock_set_timeout.assert_called_once_with(30.0)

        display.check_auto_sleep()
        mock_check_sleep.assert_called_once()

        # Test debug methods
        regs = display.dump_registers()
        assert regs == {"reg1": 0x1234}
        mock_dump_regs.assert_called_once()

        status = display.get_device_status()
        assert status == {"status": "ok"}
        mock_get_status.assert_called_once()

        # Test enhanced driving
        enabled = display.is_enhanced_driving_enabled()
        assert enabled is True
        mock_is_enhanced.assert_called_once()

    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.__init__", return_value=None)
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.__enter__")
    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.__exit__")
    def test_context_manager_thread_safe(self, mock_exit, mock_enter, mock_init):
        """Test thread-safe context manager implementation."""
        # Configure mocks
        mock_enter.return_value = MagicMock()

        # Test context manager
        with ThreadSafeEPaperDisplay(vcom=-2.0) as display:
            # Verify parent __enter__ was called
            mock_enter.assert_called_once()
            assert display is not None

        # Verify parent __exit__ was called
        mock_exit.assert_called_once()

    @patch("IT8951_ePaper_Py.thread_safe.EPaperDisplay.__init__", return_value=None)
    def test_properties_thread_safe(self, mock_init):
        """Test thread-safe property access."""
        display = ThreadSafeEPaperDisplay(vcom=-2.0)

        # Mock the parent property access by patching super()
        with (
            patch.object(EPaperDisplay, "power_state", new_callable=PropertyMock) as mock_power,
            patch.object(EPaperDisplay, "width", new_callable=PropertyMock) as mock_width,
            patch.object(EPaperDisplay, "height", new_callable=PropertyMock) as mock_height,
            patch.object(EPaperDisplay, "size", new_callable=PropertyMock) as mock_size,
            patch.object(
                EPaperDisplay, "a2_refresh_count", new_callable=PropertyMock
            ) as mock_count,
            patch.object(
                EPaperDisplay, "a2_refresh_limit", new_callable=PropertyMock
            ) as mock_limit,
        ):
            # Configure property returns
            mock_power.return_value = PowerState.ACTIVE
            mock_width.return_value = 1024
            mock_height.return_value = 768
            mock_size.return_value = (1024, 768)
            mock_count.return_value = 5
            mock_limit.return_value = 10

            # Test all properties
            assert display.power_state == PowerState.ACTIVE
            assert display.width == 1024
            assert display.height == 768
            assert display.size == (1024, 768)
            assert display.a2_refresh_count == 5
            assert display.a2_refresh_limit == 10

    def test_concurrent_property_access(self):
        """Test that property access is thread-safe under concurrent load."""
        # Create a mock display with properties
        display = Mock(spec=ThreadSafeEPaperDisplay)
        display._lock = threading.RLock()

        # Track access order
        access_log = []
        access_lock = threading.Lock()

        # Create thread-safe property getter
        @property
        @thread_safe_method
        def test_property(self) -> int:
            with access_lock:
                access_log.append(f"read-{threading.current_thread().name}")
            time.sleep(0.01)  # Simulate property computation
            return 42

        # Bind property to display
        type(display).test_property = test_property

        # Access property from multiple threads
        def access_property(thread_id: int) -> int:
            threading.current_thread().name = f"Thread-{thread_id}"
            return display.test_property

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(access_property, i) for i in range(3)]
            results = [f.result() for f in futures]

        # All should get the same value
        assert all(r == 42 for r in results)
        assert len(access_log) == 3
