# Error Recovery Procedures

This guide provides comprehensive error recovery procedures for the IT8951 e-paper driver, helping you build robust applications that handle failures gracefully.

## Table of Contents

- [Overview](#overview)
- [Common Error Types](#common-error-types)
- [Retry Policies](#retry-policies)
- [Recovery Strategies](#recovery-strategies)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Overview

The IT8951 e-paper driver provides multiple layers of error recovery:

1. **Automatic Retries**: Built-in retry mechanisms for transient failures
2. **Configurable Policies**: Flexible retry strategies for different scenarios
3. **Fallback Mechanisms**: Progressive degradation when primary methods fail
4. **State Recovery**: Procedures to recover from unknown states

## Common Error Types

### Communication Errors

Communication errors occur when SPI communication fails:

```python
from IT8951_ePaper_Py import CommunicationError, RetryPolicy, create_retry_spi_interface

# Create SPI with retry capability
retry_policy = RetryPolicy(max_attempts=5, delay=0.1)
spi = create_retry_spi_interface(retry_policy=retry_policy)
```

**Recovery Steps:**

1. Automatic retry with configurable backoff
2. Hardware reset if retries fail
3. Full reinitialization as last resort

### Timeout Errors

Timeouts occur when the device doesn't respond within expected time:

```python
from IT8951_ePaper_Py import IT8951TimeoutError

try:
    display.wait_display_ready(timeout_ms=10000)
except IT8951TimeoutError:
    # Device is busy - wait and retry
    time.sleep(1)
    display.wait_display_ready(timeout_ms=30000)
```

**Recovery Steps:**

1. Increase timeout duration
2. Check device power state
3. Perform hardware reset

### Memory Errors

Memory errors occur when operations exceed available memory:

```python
from IT8951_ePaper_Py import IT8951MemoryError

try:
    display.display_image(large_image)
except IT8951MemoryError:
    # Use progressive loading instead
    display.display_image_progressive(large_image, chunk_height=100)
```

**Recovery Steps:**

1. Use progressive loading for large images
2. Reduce bit depth (8bpp → 4bpp → 2bpp → 1bpp)
3. Clear display to free memory

## Retry Policies

### Backoff Strategies

The driver supports multiple backoff strategies:

```python
from IT8951_ePaper_Py import RetryPolicy, BackoffStrategy

# Fixed delay (no backoff)
fixed_policy = RetryPolicy(
    max_attempts=3,
    delay=0.5,
    backoff_strategy=BackoffStrategy.FIXED
)

# Linear backoff (delay increases linearly)
linear_policy = RetryPolicy(
    max_attempts=5,
    delay=0.1,
    backoff_strategy=BackoffStrategy.LINEAR
)

# Exponential backoff (delay doubles each time)
exponential_policy = RetryPolicy(
    max_attempts=4,
    delay=0.1,
    backoff_factor=2.0,
    backoff_strategy=BackoffStrategy.EXPONENTIAL
)

# Exponential with jitter (adds randomness)
jitter_policy = RetryPolicy(
    max_attempts=5,
    delay=0.1,
    backoff_factor=1.5,
    backoff_strategy=BackoffStrategy.JITTER,
    jitter_range=0.1  # ±10% randomness
)
```

### Choosing a Strategy

- **Fixed**: Best for predictable, short-duration issues
- **Linear**: Good for gradually increasing load
- **Exponential**: Ideal for network/communication issues
- **Jitter**: Prevents thundering herd problems

### Advanced Configuration

```python
# Configure maximum delay to prevent excessive waits
policy = RetryPolicy(
    max_attempts=10,
    delay=0.1,
    backoff_factor=2.0,
    max_delay=5.0  # Caps delay at 5 seconds
)

# Retry only specific exceptions
policy = RetryPolicy(
    exceptions=(CommunicationError,)  # Don't retry timeouts
)
```

## Recovery Strategies

### 1. Power State Recovery

Recover from sleep or standby states:

```python
def recover_power_state(display):
    """Ensure display is in active state."""
    try:
        status = display.get_device_status()
        if status["power_state"] != PowerState.ACTIVE:
            display.wake()
            time.sleep(0.5)
            return True
    except Exception as e:
        logging.error(f"Power recovery failed: {e}")
        return False
```

### 2. Progressive Quality Degradation

Fall back to simpler display modes:

```python
def display_with_fallback(display, image, x=0, y=0):
    """Try display modes from best to worst quality."""
    modes = [
        DisplayMode.GC16,  # Full quality
        DisplayMode.GL16,  # Reduced quality
        DisplayMode.DU,    # Fast update
        DisplayMode.A2     # Binary mode
    ]

    for mode in modes:
        try:
            display.display_partial(image, x, y, mode=mode)
            return True
        except Exception as e:
            logging.warning(f"Mode {mode} failed: {e}")
            continue

    return False
```

### 3. Memory Recovery

Free memory when operations fail:

```python
def recover_from_memory_error(display):
    """Attempt to free display memory."""
    try:
        # Clear display buffer
        display.clear()
        time.sleep(0.5)

        # Force garbage collection
        import gc
        gc.collect()

        return True
    except Exception:
        return False
```

### 4. Full Reinitialization

Last resort when other recovery fails:

```python
def reinitialize_display(vcom, max_attempts=3):
    """Completely reinitialize the display."""
    for attempt in range(max_attempts):
        try:
            display = EPaperDisplay(vcom=vcom)
            display.init()
            return display
        except Exception as e:
            logging.error(f"Init attempt {attempt+1} failed: {e}")
            time.sleep(1)

    raise InitializationError("Failed to reinitialize display")
```

## Best Practices

### 1. Layer Your Defenses

```python
# Primary: Retry at SPI level
spi = create_retry_spi_interface(retry_policy=RetryPolicy())

# Secondary: Handle errors at display level
try:
    display = EPaperDisplay(vcom=-2.0, spi_interface=spi)
except CommunicationError:
    # Fallback logic
    pass

# Tertiary: Application-level recovery
def safe_display_operation(func, *args, **kwargs):
    for attempt in range(3):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(1)
```

### 2. Log for Diagnostics

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitored_operation(display, operation, *args):
    start_time = time.time()
    try:
        result = getattr(display, operation)(*args)
        duration = time.time() - start_time
        logger.info(f"{operation} succeeded in {duration:.2f}s")
        return result
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"{operation} failed after {duration:.2f}s: {e}")
        raise
```

### 3. Implement Circuit Breakers

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False

    def call(self, func, *args, **kwargs):
        if self.is_open:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.is_open = False
                self.failure_count = 0
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.is_open = True

            raise
```

### 4. Graceful Degradation

```python
class GracefulDisplay:
    def __init__(self, display):
        self.display = display
        self.quality_level = 3  # Start at highest quality

    def adaptive_display(self, image, x=0, y=0):
        """Automatically adjust quality based on success rate."""
        quality_modes = [
            (DisplayMode.A2, 1),     # Lowest quality
            (DisplayMode.DU, 2),     # Medium quality
            (DisplayMode.GL16, 4),   # High quality
            (DisplayMode.GC16, 8)    # Highest quality
        ]

        # Try current quality level
        mode, bpp = quality_modes[self.quality_level]

        try:
            self.display.display_partial(image, x, y, mode=mode)
            # Success - try to increase quality next time
            if self.quality_level < 3:
                self.quality_level += 1
        except Exception as e:
            # Failure - decrease quality
            if self.quality_level > 0:
                self.quality_level -= 1
                # Retry with lower quality
                mode, bpp = quality_modes[self.quality_level]
                self.display.display_partial(image, x, y, mode=mode)
            else:
                raise
```

## Examples

### Complete Error-Resilient Application

```python
#!/usr/bin/env python3
"""Error-resilient e-paper application."""

import logging
import time
from contextlib import contextmanager

from PIL import Image

from IT8951_ePaper_Py import (
    BackoffStrategy,
    EPaperDisplay,
    RetryPolicy,
    create_retry_spi_interface,
)

logger = logging.getLogger(__name__)


@contextmanager
def resilient_display(vcom=-2.0, max_init_attempts=3):
    """Create display with comprehensive error handling."""
    display = None

    # Try different strategies for initialization
    strategies = [
        BackoffStrategy.EXPONENTIAL,
        BackoffStrategy.LINEAR,
        BackoffStrategy.FIXED
    ]

    for strategy in strategies:
        try:
            policy = RetryPolicy(
                max_attempts=5,
                delay=0.2,
                backoff_strategy=strategy
            )
            spi = create_retry_spi_interface(retry_policy=policy)
            display = EPaperDisplay(vcom=vcom, spi_interface=spi)
            display.init()
            break
        except Exception as e:
            logger.warning(f"Init failed with {strategy}: {e}")
            continue

    if not display:
        raise Exception("Failed to initialize display")

    try:
        yield display
    finally:
        if display:
            try:
                display.close()
            except Exception as e:
                logger.error(f"Error closing display: {e}")


def main():
    """Run resilient application."""
    with resilient_display() as display:
        # Your application logic here
        img = Image.new("L", (400, 300), 255)

        # Display with automatic fallback
        for mode in [DisplayMode.GC16, DisplayMode.DU, DisplayMode.A2]:
            try:
                display.display_partial(img, mode=mode)
                break
            except Exception as e:
                logger.warning(f"Mode {mode} failed: {e}")
                continue


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
```

## See Also

- [examples/retry_demo.py](../examples/retry_demo.py) - Basic retry demonstration
- [examples/error_recovery_demo.py](../examples/error_recovery_demo.py) - Advanced recovery techniques
- [Thread Safety Guide](THREAD_SAFETY.md) - Concurrent error handling
- [Performance Guide](PERFORMANCE_GUIDE.md) - Performance impact of retries
