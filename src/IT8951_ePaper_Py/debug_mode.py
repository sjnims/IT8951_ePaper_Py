"""Debug mode configuration and utilities.

This module provides configurable debug logging for the IT8951 driver,
allowing users to control verbosity levels for different components.
"""

import contextlib
import logging
import os
from collections.abc import Callable
from enum import IntEnum
from functools import wraps
from typing import Any, ClassVar, TypeVar

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


class DebugLevel(IntEnum):
    """Debug verbosity levels."""

    OFF = 0  # No debug output
    ERROR = 10  # Only errors
    WARNING = 20  # Warnings and errors
    INFO = 30  # General information
    DEBUG = 40  # Detailed debug info
    TRACE = 50  # Very detailed trace info


class DebugMode:
    """Manage debug mode configuration for the IT8951 driver."""

    _instance: ClassVar["DebugMode | None"] = None
    _debug_level: DebugLevel = DebugLevel.OFF
    _logger: logging.Logger | None = None
    _component_levels: ClassVar[dict[str, DebugLevel]] = {}

    def __new__(cls) -> "DebugMode":
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize debug mode configuration."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._setup_logger()
            self._check_env_vars()

    def _setup_logger(self) -> None:
        """Set up the logger with appropriate handlers."""
        self._logger = logging.getLogger("IT8951")
        self._logger.setLevel(logging.DEBUG)  # Allow all levels through

        # Remove existing handlers to avoid duplicates
        self._logger.handlers.clear()

        # Create console handler with custom formatter
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - IT8951.%(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def _check_env_vars(self) -> None:
        """Check environment variables for debug configuration."""
        # Global debug level
        if env_level := os.getenv("IT8951_DEBUG"):
            with contextlib.suppress(KeyError, ValueError):
                self.set_level(DebugLevel[env_level.upper()])

        # Component-specific levels
        for key, value in os.environ.items():
            if key.startswith("IT8951_DEBUG_"):
                component = key[13:].lower()  # Remove prefix
                with contextlib.suppress(KeyError, ValueError):
                    self.set_component_level(component, DebugLevel[value.upper()])

    def set_level(self, level: DebugLevel) -> None:
        """Set global debug level.

        Args:
            level: Debug verbosity level.
        """
        self._debug_level = level
        if self._logger:
            self._logger.setLevel(self._get_logging_level(level))

    def get_level(self) -> DebugLevel:
        """Get current global debug level."""
        return self._debug_level

    def set_component_level(self, component: str, level: DebugLevel) -> None:
        """Set debug level for a specific component.

        Args:
            component: Component name (e.g., 'spi', 'display', 'power').
            level: Debug verbosity level for this component.
        """
        self._component_levels[component.lower()] = level

    def get_component_level(self, component: str) -> DebugLevel:
        """Get debug level for a specific component."""
        return self._component_levels.get(component.lower(), self._debug_level)

    def is_enabled(self, level: DebugLevel, component: str | None = None) -> bool:
        """Check if debug output is enabled for a given level and component."""
        if component:
            component_level = self.get_component_level(component)
            return level <= component_level
        return level <= self._debug_level

    @staticmethod
    def _get_logging_level(debug_level: DebugLevel) -> int:
        """Convert DebugLevel to Python logging level."""
        # Define a custom TRACE level below DEBUG
        trace_level = 5

        mapping = {
            DebugLevel.OFF: logging.CRITICAL + 10,  # Effectively disable
            DebugLevel.ERROR: logging.ERROR,
            DebugLevel.WARNING: logging.WARNING,
            DebugLevel.INFO: logging.INFO,
            DebugLevel.DEBUG: logging.DEBUG,
            DebugLevel.TRACE: trace_level,  # Custom trace level
        }
        return mapping.get(debug_level, logging.INFO)

    def log(
        self,
        level: DebugLevel,
        message: str,
        component: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Log a message at the specified level.

        Args:
            level: Debug level for this message.
            message: Message to log.
            component: Optional component name.
            **kwargs: Additional context for the message.
        """
        if not self.is_enabled(level, component):
            return

        if self._logger:
            # Add component to logger name
            logger = self._logger
            if component:
                logger = self._logger.getChild(component)

            # Convert to Python logging level
            log_level = self._get_logging_level(level)

            # Add context if provided
            if kwargs:
                extra_info = " | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())
                message += extra_info

            logger.log(log_level, message)

    def trace(self, message: str, component: str | None = None, **kwargs: Any) -> None:
        """Log trace-level message (most verbose)."""
        self.log(DebugLevel.TRACE, message, component, **kwargs)

    def debug(self, message: str, component: str | None = None, **kwargs: Any) -> None:
        """Log debug-level message."""
        self.log(DebugLevel.DEBUG, message, component, **kwargs)

    def info(self, message: str, component: str | None = None, **kwargs: Any) -> None:
        """Log info-level message."""
        self.log(DebugLevel.INFO, message, component, **kwargs)

    def warning(self, message: str, component: str | None = None, **kwargs: Any) -> None:
        """Log warning-level message."""
        self.log(DebugLevel.WARNING, message, component, **kwargs)

    def error(self, message: str, component: str | None = None, **kwargs: Any) -> None:
        """Log error-level message."""
        self.log(DebugLevel.ERROR, message, component, **kwargs)


# Global debug mode instance
debug_mode = DebugMode()


def debug_method(component: str | None = None) -> Callable[[F], F]:
    """Decorator to add debug logging to methods.

    Args:
        component: Optional component name for logging.

    Returns:
        Decorated function with debug logging.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Only log if debug or trace is enabled
            if not debug_mode.is_enabled(DebugLevel.DEBUG, component):
                return func(*args, **kwargs)

            # Get method name and class if available
            method_name = func.__name__
            if args and hasattr(args[0], "__class__"):
                method_name = f"{args[0].__class__.__name__}.{method_name}"

            # Log entry
            debug_mode.debug(f"Entering {method_name}", component, args=args[1:], kwargs=kwargs)

            try:
                # Execute method
                result = func(*args, **kwargs)

                # Log exit
                debug_mode.debug(f"Exiting {method_name}", component, result=result)
                return result

            except Exception as e:
                # Log exception
                debug_mode.error(f"Exception in {method_name}: {e}", component)
                raise

        return wrapper  # type: ignore

    return decorator


def debug_timing(component: str | None = None) -> Callable[[F], F]:
    """Decorator to add timing debug information.

    Args:
        component: Optional component name for logging.

    Returns:
        Decorated function with timing information.
    """
    import time

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Only time if info level or higher is enabled
            if not debug_mode.is_enabled(DebugLevel.INFO, component):
                return func(*args, **kwargs)

            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.perf_counter() - start_time) * 1000  # Convert to ms

                # Log timing
                method_name = func.__name__
                if args and hasattr(args[0], "__class__"):
                    method_name = f"{args[0].__class__.__name__}.{method_name}"

                debug_mode.info(f"{method_name} completed", component, elapsed_ms=f"{elapsed:.2f}")
                return result

            except Exception:
                elapsed = (time.perf_counter() - start_time) * 1000
                debug_mode.error(f"{func.__name__} failed", component, elapsed_ms=f"{elapsed:.2f}")
                raise

        return wrapper  # type: ignore

    return decorator


# Convenience functions for enabling debug mode
def enable_debug(level: DebugLevel = DebugLevel.DEBUG) -> None:
    """Enable debug mode with specified level.

    Args:
        level: Debug verbosity level (default: DEBUG).
    """
    debug_mode.set_level(level)


def disable_debug() -> None:
    """Disable debug mode."""
    debug_mode.set_level(DebugLevel.OFF)


def set_component_debug(component: str, level: DebugLevel) -> None:
    """Set debug level for a specific component.

    Args:
        component: Component name (e.g., 'spi', 'display', 'power').
        level: Debug verbosity level.
    """
    debug_mode.set_component_level(component, level)
