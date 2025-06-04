#!/usr/bin/env python3
"""Demonstrate advanced error recovery mechanisms for IT8951 e-paper displays.

This example shows comprehensive error recovery strategies including:
- Different backoff strategies for retry policies
- Recovery from communication failures
- Handling memory errors gracefully
- Power state recovery procedures
- Progressive degradation of display quality
"""

import logging
import time

from PIL import Image, ImageDraw, ImageFont

from IT8951_ePaper_Py import (
    BackoffStrategy,
    CommunicationError,
    EPaperDisplay,
    IT8951MemoryError,
    IT8951TimeoutError,
    RetryPolicy,
    create_retry_spi_interface,
)
from IT8951_ePaper_Py.constants import DisplayMode, PowerState

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class RobustEPaperDisplay:
    """EPaper display wrapper with advanced error recovery capabilities."""

    def __init__(self, vcom: float, max_recovery_attempts: int = 3) -> None:
        """Initialize robust display with recovery mechanisms.

        Args:
            vcom: VCOM voltage for the display.
            max_recovery_attempts: Maximum number of recovery attempts.
        """
        self.vcom = vcom
        self.max_recovery_attempts = max_recovery_attempts
        self.display: EPaperDisplay | None = None
        self.recovery_count = 0
        self.last_known_state: dict[str, object] = {}

    def _create_display_with_strategy(self, strategy: BackoffStrategy) -> EPaperDisplay:
        """Create display with specific retry strategy.

        Args:
            strategy: Backoff strategy to use.

        Returns:
            Configured EPaperDisplay instance.
        """
        logger.info(f"Creating display with {strategy.value} backoff strategy")

        retry_policy = RetryPolicy(
            max_attempts=5,
            delay=0.1,
            backoff_factor=1.5,
            backoff_strategy=strategy,
            max_delay=2.0,
            jitter_range=0.1 if strategy == BackoffStrategy.JITTER else 0.0,
        )

        spi = create_retry_spi_interface(retry_policy=retry_policy)
        return EPaperDisplay(vcom=self.vcom, spi_interface=spi)

    def initialize_with_recovery(self) -> tuple[int, int]:
        """Initialize display with automatic recovery on failure.

        Returns:
            Display dimensions (width, height).

        Raises:
            CommunicationError: If all recovery attempts fail.
        """
        strategies = [
            BackoffStrategy.EXPONENTIAL,  # Start with standard exponential
            BackoffStrategy.LINEAR,  # Fall back to linear
            BackoffStrategy.JITTER,  # Try with jitter
            BackoffStrategy.FIXED,  # Last resort: fixed delays
        ]

        last_error: Exception | None = None

        for i, strategy in enumerate(strategies):
            try:
                logger.info(f"Initialization attempt {i + 1}/{len(strategies)}")

                # Clean up previous display if exists
                if self.display:
                    try:
                        self.display.close()
                    except Exception as cleanup_error:
                        logger.debug(f"Error closing previous display: {cleanup_error}")

                # Create new display with current strategy
                self.display = self._create_display_with_strategy(strategy)
                width, height = self.display.init()

                logger.info(f"Display initialized successfully: {width}x{height}")
                return width, height

            except (CommunicationError, IT8951TimeoutError) as e:
                last_error = e
                logger.warning(f"Initialization failed with {strategy.value}: {e}")

                if i < len(strategies) - 1:
                    logger.info("Trying next recovery strategy...")
                    time.sleep(0.5 * (i + 1))  # Progressive delay between strategies

        raise CommunicationError(f"Failed to initialize after all strategies: {last_error}")

    def display_with_fallback(self, image: Image.Image, x: int = 0, y: int = 0) -> None:
        """Display image with fallback to simpler modes on failure.

        Args:
            image: Image to display.
            x: X coordinate.
            y: Y coordinate.
        """
        if not self.display:
            raise ValueError("Display not initialized")

        # Try display modes from best to worst quality
        modes = [
            (DisplayMode.GC16, "Full quality (GC16)"),
            (DisplayMode.GL16, "Reduced quality (GL16)"),
            (DisplayMode.DU, "Fast update (DU)"),
            (DisplayMode.A2, "Binary mode (A2)"),
        ]

        last_error: Exception | None = None

        for mode, description in modes:
            try:
                logger.info(f"Attempting display with {description}")
                self.display.display_partial(image, x, y, mode=mode)
                logger.info(f"Successfully displayed with {description}")
                return

            except IT8951MemoryError as e:
                last_error = e
                logger.warning(f"Memory error with {description}: {e}")

                # Try to free memory and retry
                if self._recover_from_memory_error():
                    try:
                        self.display.display_partial(image, x, y, mode=mode)
                        logger.info(f"Retry successful with {description}")
                        return
                    except Exception as retry_error:
                        logger.debug(f"Retry after memory recovery failed: {retry_error}")

            except Exception as e:
                last_error = e
                logger.warning(f"Failed with {description}: {e}")

        raise CommunicationError(f"All display modes failed: {last_error}")

    def _recover_from_memory_error(self) -> bool:
        """Attempt to recover from memory errors.

        Returns:
            True if recovery was successful.
        """
        if not self.display:
            return False

        logger.info("Attempting memory error recovery...")

        try:
            # Clear display to free memory
            self.display.clear()
            time.sleep(0.5)

            # Force garbage collection
            import gc

            gc.collect()

            logger.info("Memory recovery successful")
            return True

        except Exception as e:
            logger.error(f"Memory recovery failed: {e}")
            return False

    def recover_power_state(self) -> bool:
        """Recover display from unknown power state.

        Returns:
            True if recovery successful.
        """
        if not self.display:
            return False

        logger.info("Attempting power state recovery...")

        try:
            # Try to get current state
            status = self.display.get_device_status()
            current_state = status.get("power_state", PowerState.ACTIVE)
            logger.info(f"Current power state: {current_state}")

            # Wake if needed
            if current_state != PowerState.ACTIVE:
                logger.info("Waking display...")
                self.display.wake()
                time.sleep(0.5)

            # Verify active
            status = self.display.get_device_status()
            if status.get("power_state") == PowerState.ACTIVE:
                logger.info("Power state recovery successful")
                return True

        except Exception as e:
            logger.error(f"Power state recovery failed: {e}")

        return False

    def safe_operation(self, operation: str, *args: object, **kwargs: object) -> object:
        """Execute operation with full error recovery.

        Args:
            operation: Method name to call on display.
            *args: Positional arguments for the method.
            **kwargs: Keyword arguments for the method.

        Returns:
            Result of the operation.
        """
        if not self.display:
            raise ValueError("Display not initialized")

        for attempt in range(self.max_recovery_attempts):
            try:
                method = getattr(self.display, operation)
                result = method(*args, **kwargs)
                self.recovery_count = 0  # Reset on success
                return result

            except (CommunicationError, IT8951TimeoutError) as e:
                logger.warning(f"Operation '{operation}' failed (attempt {attempt + 1}): {e}")

                if attempt < self.max_recovery_attempts - 1:
                    # Try power state recovery
                    if self.recover_power_state():
                        continue

                    # Try full reinitialization
                    try:
                        logger.info("Attempting full reinitialization...")
                        self.initialize_with_recovery()
                        continue
                    except Exception as reinit_error:
                        logger.error(f"Reinitialization failed: {reinit_error}")

                raise

        # This should never be reached due to the raise above
        raise RuntimeError("Unexpected end of safe_operation retry loop")

    def close(self) -> None:
        """Safely close the display."""
        if self.display:
            try:
                self.display.close()
            except Exception as e:
                logger.error(f"Error closing display: {e}")


def create_status_image(width: int, height: int, message: str) -> Image.Image:
    """Create a status image with message."""
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    # Try to use a nice font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except Exception:
        font = ImageFont.load_default()

    # Draw border
    draw.rectangle([(10, 10), (width - 10, height - 10)], outline=0, width=2)

    # Draw message
    draw.text((width // 2, height // 2), message, fill=0, font=font, anchor="mm")

    return img


def demonstrate_recovery_strategies() -> None:
    """Demonstrate various error recovery strategies."""
    logger.info("=== Error Recovery Demo ===")

    # Create robust display wrapper
    robust_display = RobustEPaperDisplay(vcom=-2.0)

    try:
        # Initialize with automatic recovery
        logger.info("\n1. Testing initialization with recovery...")
        width, height = robust_display.initialize_with_recovery()
        logger.info(f"Display ready: {width}x{height}")

        # Test memory error recovery
        logger.info("\n2. Testing memory error recovery...")
        large_image = create_status_image(400, 300, "Memory Test")
        robust_display.display_with_fallback(large_image, x=100, y=100)

        # Test power state recovery
        logger.info("\n3. Testing power state recovery...")
        if robust_display.display:
            # Put display to sleep
            robust_display.display.sleep()
            time.sleep(1)

            # Try operation that requires active state
            status_img = create_status_image(300, 200, "Power Recovery")
            robust_display.safe_operation(
                "display_partial", status_img, x=150, y=150, mode=DisplayMode.DU
            )

        # Test progressive quality degradation
        logger.info("\n4. Testing progressive quality degradation...")
        test_img = create_status_image(350, 250, "Quality Fallback")
        robust_display.display_with_fallback(test_img, x=125, y=125)

        # Test safe operations
        logger.info("\n5. Testing safe operations...")
        robust_display.safe_operation("clear")

        final_img = create_status_image(400, 200, "Recovery Demo Complete!")
        robust_display.safe_operation(
            "display_partial", final_img, x=(width - 400) // 2, y=(height - 200) // 2
        )

    finally:
        robust_display.close()


def demonstrate_retry_policies() -> None:
    """Demonstrate different retry policies in action."""
    logger.info("\n=== Retry Policy Comparison ===")

    strategies = [
        (BackoffStrategy.FIXED, "Fixed delay (no backoff)"),
        (BackoffStrategy.LINEAR, "Linear backoff"),
        (BackoffStrategy.EXPONENTIAL, "Exponential backoff"),
        (BackoffStrategy.JITTER, "Exponential with jitter"),
    ]

    for strategy, description in strategies:
        logger.info(f"\nTesting {description}")

        policy = RetryPolicy(
            max_attempts=4,
            delay=0.1,
            backoff_factor=2.0,
            backoff_strategy=strategy,
            max_delay=1.0,
            jitter_range=0.2,
        )

        # Show calculated delays
        logger.info("Calculated delays for each retry:")
        for attempt in range(3):
            delay = policy.calculate_delay(attempt)
            logger.info(f"  Attempt {attempt + 1}: {delay:.3f}s")


def main() -> None:
    """Run error recovery demonstrations."""
    logger.info("Starting IT8951 Error Recovery Demo")
    logger.info("This demo shows advanced error handling and recovery")

    # Show retry policy comparison
    demonstrate_retry_policies()

    # Demonstrate recovery strategies
    demonstrate_recovery_strategies()

    logger.info("\nError recovery demo completed!")
    logger.info("Key takeaways:")
    logger.info("- Use appropriate backoff strategies for your use case")
    logger.info("- Implement fallback mechanisms for critical operations")
    logger.info("- Handle power state transitions gracefully")
    logger.info("- Degrade quality progressively when resources are limited")


if __name__ == "__main__":
    main()
