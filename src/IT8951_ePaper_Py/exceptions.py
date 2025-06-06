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
    ├── IT8951TimeoutError - Operation timeouts
    └── VCOMError - VCOM voltage configuration errors

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
    """Base exception for all IT8951-related errors.

    Attributes:
        context: Optional diagnostic context for the error.
    """

    def __init__(self, message: str, context: dict[str, object] | None = None) -> None:
        """Initialize with message and optional context.

        Args:
            message: Error message.
            context: Optional diagnostic context.
        """
        super().__init__(message)
        self.context = context or {}

    def __str__(self) -> str:
        """Return string representation with context if available."""
        base_msg = super().__str__()
        if self.context:
            context_str = " | ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{base_msg} [{context_str}]"
        return base_msg


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


class VCOMError(IT8951Error):
    """Raised when VCOM voltage configuration or validation fails.

    VCOM (Common Voltage) must be set correctly for each display
    to ensure proper image quality and prevent display damage.
    """

    pass
