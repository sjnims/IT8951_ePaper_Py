"""Utility functions and decorators for IT8951 e-paper driver."""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def timed_operation(
    operation_name: str | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to measure and log operation timing.

    Args:
        operation_name: Optional name for the operation. If not provided,
                       uses the function name.

    Returns:
        Decorated function that logs execution time.
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
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

        return wrapper

    return decorator
