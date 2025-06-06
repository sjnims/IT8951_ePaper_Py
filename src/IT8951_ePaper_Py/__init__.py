"""IT8951 e-paper driver for Python.

A pure Python implementation of the Waveshare IT8951 e-paper controller driver,
providing a simple interface for controlling e-paper displays.

Basic Usage:
    >>> from IT8951_ePaper_Py import EPaperDisplay
    >>>
    >>> # Initialize with your display's VCOM value
    >>> display = EPaperDisplay(vcom=-2.0)
    >>> width, height = display.init()
    >>>
    >>> # Clear the display
    >>> display.clear()
    >>>
    >>> # Display an image
    >>> from PIL import Image
    >>> img = Image.open("picture.png")
    >>> display.display_image(img)
    >>>
    >>> # Clean up
    >>> display.close()

Thread Safety:
    The base EPaperDisplay class is NOT thread-safe. For multi-threaded applications,
    use ThreadSafeEPaperDisplay which provides automatic synchronization:

    >>> from IT8951_ePaper_Py import ThreadSafeEPaperDisplay
    >>> display = ThreadSafeEPaperDisplay(vcom=-2.0)
    >>> # Can be safely used from multiple threads
"""  # noqa: N999

from IT8951_ePaper_Py.debug_mode import (
    DebugLevel,
    disable_debug,
    enable_debug,
    set_component_debug,
)
from IT8951_ePaper_Py.display import EPaperDisplay
from IT8951_ePaper_Py.exceptions import (
    CommunicationError,
    DeviceError,
    DisplayError,
    InitializationError,
    InvalidParameterError,
    IT8951Error,
    IT8951MemoryError,
    IT8951TimeoutError,
    VCOMError,
)
from IT8951_ePaper_Py.retry_policy import (
    BackoffStrategy,
    RetryPolicy,
    RetrySPIInterface,
    create_retry_spi_interface,
)
from IT8951_ePaper_Py.thread_safe import ThreadSafeEPaperDisplay

__version__ = "0.14.1"
__all__ = [
    "BackoffStrategy",
    "CommunicationError",
    "DebugLevel",
    "DeviceError",
    "DisplayError",
    "EPaperDisplay",
    "IT8951Error",
    "IT8951MemoryError",
    "IT8951TimeoutError",
    "InitializationError",
    "InvalidParameterError",
    "RetryPolicy",
    "RetrySPIInterface",
    "ThreadSafeEPaperDisplay",
    "VCOMError",
    "create_retry_spi_interface",
    "disable_debug",
    "enable_debug",
    "set_component_debug",
]
