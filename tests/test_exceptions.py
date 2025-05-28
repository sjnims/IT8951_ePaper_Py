"""Tests for exception hierarchy."""

import pytest

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


class TestExceptions:
    """Test exception hierarchy."""

    def test_base_exception(self) -> None:
        """Test base IT8951Error."""
        with pytest.raises(IT8951Error):
            raise IT8951Error("Test error")

    def test_communication_error(self) -> None:
        """Test CommunicationError inherits from IT8951Error."""
        error = CommunicationError("SPI failed")
        assert isinstance(error, IT8951Error)
        assert str(error) == "SPI failed"

    def test_device_error(self) -> None:
        """Test DeviceError inherits from IT8951Error."""
        error = DeviceError("Device not responding")
        assert isinstance(error, IT8951Error)
        assert str(error) == "Device not responding"

    def test_initialization_error(self) -> None:
        """Test InitializationError inherits from IT8951Error."""
        error = InitializationError("Init failed")
        assert isinstance(error, IT8951Error)
        assert str(error) == "Init failed"

    def test_display_error(self) -> None:
        """Test DisplayError inherits from IT8951Error."""
        error = DisplayError("Display failed")
        assert isinstance(error, IT8951Error)
        assert str(error) == "Display failed"

    def test_memory_error(self) -> None:
        """Test IT8951MemoryError inherits from IT8951Error."""
        error = IT8951MemoryError("Memory allocation failed")
        assert isinstance(error, IT8951Error)
        assert str(error) == "Memory allocation failed"

    def test_invalid_parameter_error(self) -> None:
        """Test InvalidParameterError inherits from IT8951Error."""
        error = InvalidParameterError("Invalid parameter")
        assert isinstance(error, IT8951Error)
        assert str(error) == "Invalid parameter"

    def test_timeout_error(self) -> None:
        """Test IT8951TimeoutError inherits from IT8951Error."""
        error = IT8951TimeoutError("Operation timeout")
        assert isinstance(error, IT8951Error)
        assert str(error) == "Operation timeout"

    def test_exception_chaining(self) -> None:
        """Test exception chaining works correctly."""
        original = ValueError("Original error")
        with pytest.raises(CommunicationError) as exc_info:
            raise CommunicationError("SPI error") from original
        assert exc_info.value.__cause__ is original
        assert str(exc_info.value) == "SPI error"
