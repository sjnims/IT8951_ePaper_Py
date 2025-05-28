"""Custom exceptions for IT8951 e-paper driver."""


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
