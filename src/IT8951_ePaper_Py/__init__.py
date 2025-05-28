"""IT8951 e-paper driver for Python.

A pure Python implementation of the Waveshare IT8951 e-paper controller driver.
"""  # noqa: N999

from IT8951_ePaper_Py.display import EPaperDisplay
from IT8951_ePaper_Py.exceptions import (
    CommunicationError,
    DeviceError,
    InitializationError,
    IT8951Error,
)

__version__ = "0.1.0"
__all__ = [
    "CommunicationError",
    "DeviceError",
    "EPaperDisplay",
    "IT8951Error",
    "InitializationError",
]
