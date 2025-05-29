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
"""  # noqa: N999

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
)

__version__ = "0.2.0"
__all__ = [
    "CommunicationError",
    "DeviceError",
    "DisplayError",
    "EPaperDisplay",
    "IT8951Error",
    "IT8951MemoryError",
    "IT8951TimeoutError",
    "InitializationError",
    "InvalidParameterError",
]
