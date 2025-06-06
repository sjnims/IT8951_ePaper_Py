"""Tests for debug mode functionality."""

import logging
import os
from unittest.mock import patch

import pytest

from IT8951_ePaper_Py.debug_mode import (
    DebugLevel,
    DebugMode,
    debug_method,
    debug_mode,
    debug_timing,
    disable_debug,
    enable_debug,
    set_component_debug,
)
from IT8951_ePaper_Py.exceptions import InitializationError, IT8951Error


class TestDebugMode:
    """Test DebugMode class."""

    def setup_method(self) -> None:
        """Reset debug mode before each test."""
        disable_debug()
        # Clear any component levels
        debug_mode._component_levels.clear()

    def test_singleton_instance(self) -> None:
        """Test that DebugMode is a singleton."""
        mode1 = DebugMode()
        mode2 = DebugMode()
        assert mode1 is mode2

    def test_default_level(self) -> None:
        """Test default debug level is OFF."""
        assert debug_mode.get_level() == DebugLevel.OFF

    def test_set_get_level(self) -> None:
        """Test setting and getting debug level."""
        debug_mode.set_level(DebugLevel.DEBUG)
        assert debug_mode.get_level() == DebugLevel.DEBUG

    def test_component_level(self) -> None:
        """Test component-specific debug levels."""
        # Set global level
        debug_mode.set_level(DebugLevel.WARNING)

        # Set component level
        debug_mode.set_component_level("spi", DebugLevel.TRACE)

        # Component level should override global
        assert debug_mode.get_component_level("spi") == DebugLevel.TRACE
        # Unknown component should use global level
        assert debug_mode.get_component_level("unknown") == DebugLevel.WARNING

    def test_is_enabled(self) -> None:
        """Test debug level checking."""
        debug_mode.set_level(DebugLevel.INFO)

        # Levels at or below INFO should be enabled
        assert debug_mode.is_enabled(DebugLevel.ERROR)
        assert debug_mode.is_enabled(DebugLevel.WARNING)
        assert debug_mode.is_enabled(DebugLevel.INFO)

        # Higher levels should not be enabled
        assert not debug_mode.is_enabled(DebugLevel.DEBUG)
        assert not debug_mode.is_enabled(DebugLevel.TRACE)

    def test_is_enabled_component(self) -> None:
        """Test component-specific debug level checking."""
        debug_mode.set_level(DebugLevel.WARNING)
        debug_mode.set_component_level("display", DebugLevel.DEBUG)

        # Component should use its own level
        assert debug_mode.is_enabled(DebugLevel.DEBUG, "display")
        assert not debug_mode.is_enabled(DebugLevel.TRACE, "display")

        # Other components use global level
        assert not debug_mode.is_enabled(DebugLevel.DEBUG, "spi")
        assert debug_mode.is_enabled(DebugLevel.WARNING, "spi")

    @patch.dict(os.environ, {"IT8951_DEBUG": "INFO"})
    def test_environment_variable_global(self) -> None:
        """Test global debug level from environment variable."""
        # Create new instance to pick up env var
        new_mode = DebugMode()
        new_mode._check_env_vars()
        assert new_mode.get_level() == DebugLevel.INFO

    @patch.dict(os.environ, {"IT8951_DEBUG_SPI": "TRACE", "IT8951_DEBUG_DISPLAY": "ERROR"})
    def test_environment_variable_components(self) -> None:
        """Test component debug levels from environment variables."""
        # Create new instance to pick up env vars
        new_mode = DebugMode()
        new_mode._check_env_vars()
        assert new_mode.get_component_level("spi") == DebugLevel.TRACE
        assert new_mode.get_component_level("display") == DebugLevel.ERROR

    @patch.dict(os.environ, {"IT8951_DEBUG": "INVALID"})
    def test_invalid_environment_variable(self) -> None:
        """Test invalid environment variable values are ignored."""
        # Create new instance with invalid env var
        new_mode = DebugMode()
        new_mode._check_env_vars()
        # Should remain at default
        assert new_mode.get_level() == DebugLevel.OFF

    def test_log_methods(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test various log methods."""
        debug_mode.set_level(DebugLevel.TRACE)

        # Capture at level 5 (TRACE) to ensure we get all messages
        with caplog.at_level(5):
            debug_mode.error("Test error", "test")
            debug_mode.warning("Test warning", "test")
            debug_mode.info("Test info", "test")
            debug_mode.debug("Test debug", "test")
            debug_mode.trace("Test trace", "test")

        # All messages should be logged
        assert len(caplog.records) == 5
        assert "Test error" in caplog.text
        assert "Test warning" in caplog.text
        assert "Test info" in caplog.text
        assert "Test debug" in caplog.text
        assert "Test trace" in caplog.text

    def test_log_with_context(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test logging with additional context."""
        debug_mode.set_level(DebugLevel.INFO)

        with caplog.at_level(logging.INFO):
            debug_mode.info("Test message", "test", key1="value1", key2=42)

        assert "Test message | key1=value1 | key2=42" in caplog.text

    def test_log_filtering(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that messages are filtered by level."""
        debug_mode.set_level(DebugLevel.WARNING)

        with caplog.at_level(logging.DEBUG):
            debug_mode.debug("Should not appear", "test")
            debug_mode.info("Should not appear", "test")
            debug_mode.warning("Should appear", "test")
            debug_mode.error("Should appear", "test")

        # Only warning and error should be logged
        assert len(caplog.records) == 2
        assert "Should not appear" not in caplog.text
        assert "Should appear" in caplog.text


class TestDebugDecorators:
    """Test debug decorators."""

    def setup_method(self) -> None:
        """Reset debug mode before each test."""
        disable_debug()

    def test_debug_method_decorator(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test debug_method decorator."""
        enable_debug(DebugLevel.DEBUG)

        @debug_method("test")
        def test_function(x: int, y: int) -> int:
            return x + y

        with caplog.at_level(logging.DEBUG):
            result = test_function(3, 4)

        assert result == 7
        # Check for the actual log output format
        assert "test_function" in caplog.text
        assert "args=" in caplog.text  # Args are logged differently
        assert "result=7" in caplog.text

    def test_debug_method_decorator_disabled(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test debug_method decorator when debug is disabled."""
        disable_debug()

        @debug_method("test")
        def test_function(x: int, y: int) -> int:
            return x + y

        with caplog.at_level(logging.DEBUG):
            result = test_function(3, 4)

        assert result == 7
        # No debug output when disabled
        assert len(caplog.records) == 0

    def test_debug_method_with_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test debug_method decorator with exception."""
        enable_debug(DebugLevel.DEBUG)  # Need DEBUG to see method entry/exit

        @debug_method("test")
        def test_function() -> None:
            raise ValueError("Test error")

        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError, match="Test error"):
            test_function()

        # Check that exception was logged
        assert "test_function" in caplog.text
        assert "Test error" in caplog.text

    def test_debug_timing_decorator(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test debug_timing decorator."""
        enable_debug(DebugLevel.INFO)

        @debug_timing("test")
        def test_function() -> str:
            return "done"

        with caplog.at_level(logging.INFO):
            result = test_function()

        assert result == "done"
        assert "test_function completed" in caplog.text
        assert "elapsed_ms=" in caplog.text

    def test_debug_timing_with_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test debug_timing decorator with exception."""
        enable_debug(DebugLevel.INFO)  # Need INFO to see timing logs

        @debug_timing("test")
        def test_function() -> None:
            raise RuntimeError("Test error")

        with caplog.at_level(logging.INFO), pytest.raises(RuntimeError, match="Test error"):
            test_function()

        # Check that failure was logged with timing
        # The decorator logs even on exception
        assert len(caplog.records) > 0  # Should have at least one log
        assert "elapsed_ms=" in caplog.text


class TestConvenienceFunctions:
    """Test convenience functions."""

    def setup_method(self) -> None:
        """Reset debug mode before each test."""
        disable_debug()

    def test_enable_debug(self) -> None:
        """Test enable_debug function."""
        enable_debug()
        assert debug_mode.get_level() == DebugLevel.DEBUG

        enable_debug(DebugLevel.INFO)
        assert debug_mode.get_level() == DebugLevel.INFO

    def test_disable_debug(self) -> None:
        """Test disable_debug function."""
        enable_debug()
        assert debug_mode.get_level() == DebugLevel.DEBUG

        disable_debug()
        assert debug_mode.get_level() == DebugLevel.OFF

    def test_set_component_debug_function(self) -> None:
        """Test set_component_debug function."""
        set_component_debug("spi", DebugLevel.TRACE)
        assert debug_mode.get_component_level("spi") == DebugLevel.TRACE


class TestEnhancedExceptions:
    """Test enhanced exceptions with context."""

    def test_exception_with_context(self) -> None:
        """Test IT8951Error with diagnostic context."""
        context: dict[str, object] = {"component": "test", "value": 42}
        error = IT8951Error("Test error", context)

        assert error.context == context
        assert str(error) == "Test error [component=test | value=42]"

    def test_exception_without_context(self) -> None:
        """Test IT8951Error without context."""
        error = IT8951Error("Test error")

        assert error.context == {}
        assert str(error) == "Test error"

    def test_initialization_error_with_context(self) -> None:
        """Test InitializationError with context."""
        context: dict[str, object] = {"error_type": "TimeoutError", "power_state": "ACTIVE"}
        error = InitializationError("Init failed", context)

        assert "Init failed [error_type=TimeoutError | power_state=ACTIVE]" in str(error)
