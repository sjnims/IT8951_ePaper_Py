"""Retry policies and mechanisms for handling transient SPI failures.

This module provides configurable retry logic for SPI operations that may
fail due to transient issues like timing problems or electrical noise.

Examples:
    Basic retry with default policy::

        from IT8951_ePaper_Py.retry_policy import RetryPolicy, with_retry

        # Create a retry policy
        policy = RetryPolicy(max_attempts=3, delay=0.1)

        # Apply to a function
        @with_retry(policy)
        def unstable_operation():
            # This will be retried up to 3 times
            pass

    Using retry-enabled SPI interface::

        from IT8951_ePaper_Py.spi_interface import create_spi_interface
        from IT8951_ePaper_Py.retry_policy import RetryPolicy, RetrySPIInterface

        # Create base SPI interface
        base_spi = create_spi_interface()

        # Wrap with retry logic
        retry_spi = RetrySPIInterface(base_spi, RetryPolicy())
        retry_spi.init()

    Advanced backoff strategies::

        from IT8951_ePaper_Py.retry_policy import RetryPolicy, BackoffStrategy

        # Exponential backoff (default)
        exponential = RetryPolicy(backoff_strategy=BackoffStrategy.EXPONENTIAL)

        # Linear backoff
        linear = RetryPolicy(backoff_strategy=BackoffStrategy.LINEAR)

        # Fixed delay (no backoff)
        fixed = RetryPolicy(backoff_strategy=BackoffStrategy.FIXED)
"""

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, TypeVar

from IT8951_ePaper_Py.exceptions import CommunicationError, IT8951Error, IT8951TimeoutError
from IT8951_ePaper_Py.spi_interface import SPIInterface

F = TypeVar("F", bound=Callable[..., Any])


class BackoffStrategy(Enum):
    """Backoff strategies for retry delays."""

    FIXED = "fixed"  # No backoff, constant delay
    LINEAR = "linear"  # Linear increase (delay * attempt)
    EXPONENTIAL = "exponential"  # Exponential increase (delay * factor^attempt)
    JITTER = "jitter"  # Exponential with random jitter


@dataclass
class RetryPolicy:
    """Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of attempts (including initial).
        delay: Base delay between retries in seconds.
        backoff_factor: Multiplier for delay after each retry (for exponential/linear).
        backoff_strategy: Strategy for calculating delay between retries.
        exceptions: Tuple of exception types to retry on.
        max_delay: Maximum delay between retries (caps exponential growth).
        jitter_range: Range for random jitter (0.0-1.0), used with JITTER strategy.
    """

    max_attempts: int = 3
    delay: float = 0.1
    backoff_factor: float = 2.0
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    exceptions: tuple[type[Exception], ...] = (CommunicationError, IT8951TimeoutError)
    max_delay: float = 10.0
    jitter_range: float = 0.1

    def __post_init__(self) -> None:
        """Validate retry policy parameters."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.delay < 0:
            raise ValueError("delay must be non-negative")
        if self.backoff_factor < 1.0:
            raise ValueError("backoff_factor must be at least 1.0")
        if self.max_delay < self.delay:
            raise ValueError("max_delay must be at least as large as delay")
        if not 0.0 <= self.jitter_range <= 1.0:
            raise ValueError("jitter_range must be between 0.0 and 1.0")

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.

        Args:
            attempt: Attempt number (0-based).

        Returns:
            Delay in seconds for this attempt.
        """
        if self.backoff_strategy == BackoffStrategy.FIXED:
            delay = self.delay
        elif self.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.delay * (attempt + 1)
        elif self.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.delay * (self.backoff_factor**attempt)
        elif self.backoff_strategy == BackoffStrategy.JITTER:
            # Exponential with jitter
            base_delay = self.delay * (self.backoff_factor**attempt)
            # Using random for jitter is acceptable for retry delays (not cryptographic)
            jitter = random.uniform(-self.jitter_range, self.jitter_range) * base_delay  # noqa: S311
            delay = base_delay + jitter
        else:
            delay = self.delay

        # Cap the delay at max_delay
        return min(delay, self.max_delay)


def with_retry(policy: RetryPolicy) -> Callable[[F], F]:
    """Decorator to add retry logic to a function.

    Args:
        policy: Retry policy configuration.

    Returns:
        Decorator function.

    Example:
        >>> policy = RetryPolicy(max_attempts=3)
        >>> @with_retry(policy)
        ... def flaky_operation():
        ...     # This will be retried up to 3 times
        ...     pass
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> object:
            last_exception: Exception | None = None

            for attempt in range(policy.max_attempts):
                try:
                    return func(*args, **kwargs)
                except policy.exceptions as e:
                    last_exception = e
                    if attempt < policy.max_attempts - 1:
                        # Calculate delay for this attempt
                        delay = policy.calculate_delay(attempt)
                        time.sleep(delay)
                    else:
                        # Last attempt failed, re-raise
                        raise

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            raise IT8951Error("Retry logic error: no exception but all attempts failed")

        # Type checkers struggle with decorator typing - wrapper maintains the
        # same signature as func
        return wrapper  # type: ignore[return-value] # Decorator preserves function signature

    return decorator


class RetrySPIInterface(SPIInterface):
    """SPI interface wrapper that adds retry logic to operations.

    This wrapper adds configurable retry behavior to an existing SPI interface,
    helping to handle transient communication failures.

    Thread Safety:
        This class has the same thread safety characteristics as the wrapped
        SPI interface (i.e., NOT thread-safe).
    """

    def __init__(
        self, spi_interface: SPIInterface, retry_policy: RetryPolicy | None = None
    ) -> None:
        """Initialize retry SPI interface wrapper.

        Args:
            spi_interface: Base SPI interface to wrap.
            retry_policy: Retry policy to use. If None, uses default policy.
        """
        self._spi = spi_interface
        self._policy = retry_policy or RetryPolicy()

    def init(self) -> None:
        """Initialize SPI interface with retry logic."""
        with_retry(self._policy)(self._spi.init)()

    def close(self) -> None:
        """Close SPI interface."""
        # Close is usually idempotent, no retry needed
        self._spi.close()

    def reset(self) -> None:
        """Hardware reset with retry logic."""
        with_retry(self._policy)(self._spi.reset)()

    def wait_busy(self, timeout_ms: int = 5000) -> None:
        """Wait for device ready with retry logic."""
        # wait_busy already has timeout logic, so we use a special policy
        # that doesn't retry on timeout errors
        wait_policy = RetryPolicy(
            max_attempts=self._policy.max_attempts,
            delay=self._policy.delay,
            backoff_factor=self._policy.backoff_factor,
            exceptions=(CommunicationError,),  # Don't retry timeouts
        )
        with_retry(wait_policy)(self._spi.wait_busy)(timeout_ms)

    def write_command(self, command: int) -> None:
        """Write command with retry logic."""
        with_retry(self._policy)(self._spi.write_command)(command)

    def write_data(self, data: int) -> None:
        """Write data with retry logic."""
        with_retry(self._policy)(self._spi.write_data)(data)

    def write_data_bulk(self, data: list[int]) -> None:
        """Write bulk data with retry logic."""
        with_retry(self._policy)(self._spi.write_data_bulk)(data)

    def read_data(self) -> int:
        """Read data with retry logic."""
        return with_retry(self._policy)(self._spi.read_data)()

    def read_data_bulk(self, length: int) -> list[int]:
        """Read bulk data with retry logic."""
        return with_retry(self._policy)(self._spi.read_data_bulk)(length)


def create_retry_spi_interface(
    spi_interface: SPIInterface | None = None,
    retry_policy: RetryPolicy | None = None,
    spi_speed_hz: int | None = None,
) -> RetrySPIInterface:
    """Create an SPI interface with retry capabilities.

    Args:
        spi_interface: Base SPI interface. If None, creates default based on platform.
        retry_policy: Retry policy to use. If None, uses default policy.
        spi_speed_hz: SPI speed override (only used if spi_interface is None).

    Returns:
        SPI interface with retry capabilities.

    Example:
        >>> # Create with default settings
        >>> spi = create_retry_spi_interface()
        >>>
        >>> # Create with custom retry policy
        >>> policy = RetryPolicy(max_attempts=5, delay=0.2)
        >>> spi = create_retry_spi_interface(retry_policy=policy)
    """
    if spi_interface is None:
        from IT8951_ePaper_Py.spi_interface import create_spi_interface

        spi_interface = create_spi_interface(spi_speed_hz=spi_speed_hz)

    return RetrySPIInterface(spi_interface, retry_policy)
