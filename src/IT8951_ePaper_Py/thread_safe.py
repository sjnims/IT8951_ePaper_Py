"""Thread-safe wrapper for EPaperDisplay.

This module provides thread-safe wrappers for the IT8951 e-paper display,
allowing safe concurrent access from multiple threads.

Example:
    Using the thread-safe wrapper::

        from IT8951_ePaper_Py import ThreadSafeEPaperDisplay

        # Create a thread-safe display instance
        display = ThreadSafeEPaperDisplay(vcom=-2.0)

        # Can be safely used from multiple threads
        def worker_thread():
            display.display_image(image)

        threads = [threading.Thread(target=worker_thread) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
"""

import threading
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from types import TracebackType
from typing import Any, BinaryIO, TypeVar, cast

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from IT8951_ePaper_Py.constants import DisplayMode, PixelFormat, PowerState, Rotation
from IT8951_ePaper_Py.display import DeviceStatus, EPaperDisplay
from IT8951_ePaper_Py.spi_interface import SPIInterface

NumpyArray = NDArray[np.uint8]

# Type variable for generic function signatures
F = TypeVar("F", bound=Callable[..., Any])


def thread_safe_method(func: F) -> F:
    """Decorator to make a method thread-safe using the instance's lock.

    Args:
        func: The method to wrap with thread safety.

    Returns:
        Thread-safe version of the method.
    """

    @wraps(func)
    def wrapper(self: object, *args: object, **kwargs: object) -> object:
        if hasattr(self, "_lock"):
            # _lock is dynamically added to instances that use this decorator
            with self._lock:  # type: ignore[attr-defined] # Dynamic attribute on thread-safe classes
                return func(self, *args, **kwargs)
        return func(self, *args, **kwargs)

    return cast(F, wrapper)


class ThreadSafeEPaperDisplay(EPaperDisplay):
    """Thread-safe wrapper for EPaperDisplay.

    This class wraps all public methods of EPaperDisplay with a reentrant lock,
    ensuring thread-safe access to the display. All operations are serialized
    to prevent concurrent access to the IT8951 controller and SPI interface.

    The wrapper uses a reentrant lock (RLock) to allow nested calls within
    the same thread, which is important for methods that call other public
    methods internally.

    Thread Safety:
        This class IS thread-safe. All public methods are protected by a
        reentrant lock, ensuring only one thread can access the display
        at a time. Internal method calls within the same thread are allowed.

    Performance:
        The thread safety comes with a small performance overhead due to
        lock acquisition. For single-threaded applications, use the regular
        EPaperDisplay class instead.

    Context Manager:
        The context manager protocol is also thread-safe, but be careful
        not to share the display instance across threads during initialization
        or cleanup phases.
    """

    def __init__(
        self,
        vcom: float,
        spi_interface: SPIInterface | None = None,
        spi_speed_hz: int | None = None,
        a2_refresh_limit: int = 10,
        enhance_driving: bool = False,
    ) -> None:
        """Initialize thread-safe display wrapper.

        Args:
            vcom: VCOM voltage setting for the display
            spi_interface: Optional SPI interface (creates default if None)
            spi_speed_hz: Optional SPI speed in Hz
            a2_refresh_limit: Number of A2 mode refreshes before GC16 refresh
            enhance_driving: Enable enhanced driving mode for better quality
        """
        # Create the lock before calling parent init
        self._lock = threading.RLock()

        # Initialize parent class
        super().__init__(
            vcom=vcom,
            spi_interface=spi_interface,
            spi_speed_hz=spi_speed_hz,
            a2_refresh_limit=a2_refresh_limit,
            enhance_driving=enhance_driving,
        )

    # Override all public methods with thread-safe versions

    @thread_safe_method
    def init(self) -> tuple[int, int]:
        """Thread-safe display initialization."""
        return super().init()

    @thread_safe_method
    def close(self) -> None:
        """Thread-safe display cleanup."""
        super().close()

    @thread_safe_method
    def clear(self, color: int = 0xFF) -> None:
        """Thread-safe display clear."""
        super().clear(color)

    @thread_safe_method
    def display_image(  # noqa: PLR0913
        self,
        image: Image.Image | str | Path | BinaryIO,
        x: int = 0,
        y: int = 0,
        mode: DisplayMode = DisplayMode.GC16,
        rotation: Rotation = Rotation.ROTATE_0,
        pixel_format: PixelFormat = PixelFormat.BPP_4,
    ) -> None:
        """Thread-safe image display."""
        super().display_image(image, x, y, mode, rotation, pixel_format)

    @thread_safe_method
    def display_image_progressive(  # noqa: PLR0913
        self,
        image: Image.Image | str | Path | BinaryIO,
        x: int = 0,
        y: int = 0,
        mode: DisplayMode = DisplayMode.GC16,
        rotation: Rotation = Rotation.ROTATE_0,
        pixel_format: PixelFormat = PixelFormat.BPP_4,
        chunk_height: int = 256,
    ) -> None:
        """Thread-safe progressive image display."""
        super().display_image_progressive(image, x, y, mode, rotation, pixel_format, chunk_height)

    @thread_safe_method
    def display_partial(
        self,
        image: Image.Image | NumpyArray,
        x: int,
        y: int,
        mode: DisplayMode = DisplayMode.DU,
    ) -> None:
        """Thread-safe partial display update."""
        super().display_partial(image, x, y, mode)

    @thread_safe_method
    def set_vcom(self, voltage: float) -> None:
        """Thread-safe VCOM voltage setting."""
        super().set_vcom(voltage)

    @thread_safe_method
    def get_vcom(self) -> float:
        """Thread-safe VCOM voltage reading."""
        return super().get_vcom()

    @thread_safe_method
    def find_optimal_vcom(
        self,
        start_voltage: float = -3.0,
        end_voltage: float = -1.0,
        step: float = 0.1,
        test_pattern: Image.Image | None = None,
    ) -> float:
        """Thread-safe VCOM calibration."""
        return super().find_optimal_vcom(start_voltage, end_voltage, step, test_pattern)

    @thread_safe_method
    def sleep(self) -> None:
        """Thread-safe sleep mode entry."""
        super().sleep()

    @thread_safe_method
    def standby(self) -> None:
        """Thread-safe standby mode entry."""
        super().standby()

    @thread_safe_method
    def wake(self) -> None:
        """Thread-safe wake from sleep/standby."""
        super().wake()

    @thread_safe_method
    def set_auto_sleep_timeout(self, timeout_seconds: float | None) -> None:
        """Thread-safe auto-sleep timeout setting."""
        super().set_auto_sleep_timeout(timeout_seconds)

    @thread_safe_method
    def check_auto_sleep(self) -> None:
        """Thread-safe auto-sleep check."""
        super().check_auto_sleep()

    @thread_safe_method
    def dump_registers(self) -> dict[str, int]:
        """Thread-safe register dump."""
        return super().dump_registers()

    @thread_safe_method
    def get_device_status(self) -> DeviceStatus:
        """Thread-safe device status retrieval."""
        return super().get_device_status()

    # Thread-safe context manager support

    def __enter__(self) -> "ThreadSafeEPaperDisplay":
        """Thread-safe context manager entry."""
        with self._lock:
            super().__enter__()
            return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Thread-safe context manager exit."""
        with self._lock:
            super().__exit__(exc_type, exc_value, traceback)

    # Thread-safe property access

    @property
    @thread_safe_method
    def power_state(self) -> PowerState:
        """Thread-safe power state property."""
        return super().power_state

    @property
    @thread_safe_method
    def width(self) -> int:
        """Thread-safe width property."""
        return super().width

    @property
    @thread_safe_method
    def height(self) -> int:
        """Thread-safe height property."""
        return super().height

    @property
    @thread_safe_method
    def size(self) -> tuple[int, int]:
        """Thread-safe size property."""
        return super().size

    @property
    @thread_safe_method
    def a2_refresh_count(self) -> int:
        """Thread-safe A2 refresh count property."""
        return super().a2_refresh_count

    @property
    @thread_safe_method
    def a2_refresh_limit(self) -> int:
        """Thread-safe A2 refresh limit property."""
        return super().a2_refresh_limit

    @thread_safe_method
    def is_enhanced_driving_enabled(self) -> bool:
        """Thread-safe enhanced driving status check."""
        return super().is_enhanced_driving_enabled()
