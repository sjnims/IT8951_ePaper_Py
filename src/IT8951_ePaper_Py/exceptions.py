"""Custom exceptions for IT8951 e-paper driver.

This module defines a hierarchy of exceptions for the IT8951 driver.
All exceptions inherit from IT8951Error, making it easy to catch any
driver-related error.

Exception Hierarchy:
    IT8951Error (base)
    ├── CommunicationError - SPI communication failures
    ├── DeviceError - Hardware-reported errors
    ├── InitializationError - Setup and init failures
    ├── DisplayError - Display operation failures
    ├── IT8951MemoryError - Memory access errors
    ├── InvalidParameterError - Invalid function arguments
    └── IT8951TimeoutError - Operation timeouts

Examples:
    Catching specific errors::

        try:
            display.init()
        except InitializationError:
            print("Failed to initialize display")
        except CommunicationError:
            print("SPI communication failed")

    Catching all driver errors::

        try:
            display.display_image(img)
        except IT8951Error as e:
            print(f"Display error: {e}")
"""


class IT8951Error(Exception):
    """Base exception for all IT8951-related errors."""

    pass


class CommunicationError(IT8951Error):
    """Raised when SPI communication fails."""

    pass


class DeviceError(IT8951Error):
    """Raised when the IT8951 device reports an error."""

    pass


class InitializationError(IT8951Error):
    """Raised when device initialization fails."""

    pass


class DisplayError(IT8951Error):
    """Raised when display operations fail."""

    pass


class IT8951MemoryError(IT8951Error):
    """Raised when memory operations fail."""

    pass


class InvalidParameterError(IT8951Error):
    """Raised when invalid parameters are provided."""

    pass


class IT8951TimeoutError(IT8951Error):
    """Raised when operations timeout."""

    pass
