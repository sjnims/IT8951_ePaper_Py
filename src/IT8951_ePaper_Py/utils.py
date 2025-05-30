"""Utility functions and decorators for IT8951 e-paper driver."""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def timed_operation(operation_name: str | None = None) -> Callable[[F], F]:
    """Decorator to measure and log operation timing.

    Args:
        operation_name: Optional name for the operation. If not provided,
                       uses the function name.

    Returns:
        Decorated function that logs execution time.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            name = operation_name or func.__name__
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.perf_counter() - start_time) * 1000  # Convert to ms
                logger.debug(f"{name} completed in {elapsed:.2f}ms")
                return result
            except Exception:
                elapsed = (time.perf_counter() - start_time) * 1000
                logger.debug(f"{name} failed after {elapsed:.2f}ms")
                raise

        return wrapper  # type: ignore[return-value]

    return decorator
