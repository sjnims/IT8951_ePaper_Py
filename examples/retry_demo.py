#!/usr/bin/env python3
"""Demonstrate retry mechanism for handling transient SPI failures.

This example shows how to use the retry policy to handle transient
communication failures that might occur due to electrical noise,
timing issues, or other temporary problems.
"""

import logging
import random

from PIL import Image, ImageDraw, ImageFont

from IT8951_ePaper_Py import EPaperDisplay, RetryPolicy, create_retry_spi_interface
from IT8951_ePaper_Py.constants import DisplayMode

# Configure logging to see retry attempts
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_test_pattern(width: int, height: int) -> Image.Image:
    """Create a test pattern with random noise to simulate challenging conditions."""
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    # Draw grid pattern
    for x in range(0, width, 50):
        draw.line([(x, 0), (x, height)], fill=128, width=1)
    for y in range(0, height, 50):
        draw.line([(0, y), (width, y)], fill=128, width=1)

    # Add some text
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    except Exception:
        font = ImageFont.load_default()

    draw.text(
        (width // 2, height // 2),
        "Retry Demo",
        fill=0,
        font=font,
        anchor="mm",
    )

    # Add random noise to simulate challenging conditions
    pixels = img.load()
    if pixels:
        for _ in range(100):
            x = random.randint(0, width - 1)  # noqa: S311
            y = random.randint(0, height - 1)  # noqa: S311
            pixels[x, y] = random.randint(0, 255)  # noqa: S311

    return img


def demonstrate_basic_retry() -> None:
    """Demonstrate basic retry mechanism."""
    logger.info("=== Basic Retry Demo ===")

    # Create a retry policy with custom settings
    retry_policy = RetryPolicy(
        max_attempts=5,  # Try up to 5 times
        delay=0.2,  # Wait 200ms between attempts
        backoff_factor=1.5,  # Increase delay by 1.5x each time
    )

    # Create SPI interface with retry capability
    spi = create_retry_spi_interface(retry_policy=retry_policy)

    # Create display using the retry-enabled SPI
    with EPaperDisplay(vcom=-2.0, spi_interface=spi) as display:
        # Initialize display (will retry on failure)
        logger.info("Initializing display with retry capability...")
        width, height = display.init()
        logger.info(f"Display initialized: {width}x{height}")

        # Clear display
        logger.info("Clearing display...")
        display.clear()

        # Create and display test pattern
        logger.info("Creating test pattern...")
        img = create_test_pattern(400, 300)

        logger.info("Displaying image (with retry on failure)...")
        display.display_image(
            img,
            x=(width - 400) // 2,
            y=(height - 300) // 2,
            mode=DisplayMode.GC16,
        )

        logger.info("Display operation completed successfully!")


def demonstrate_progressive_retry() -> None:
    """Demonstrate retry with progressive policy adjustments."""
    logger.info("\n=== Progressive Retry Demo ===")

    # Start with aggressive retry policy
    aggressive_policy = RetryPolicy(
        max_attempts=10,
        delay=0.1,
        backoff_factor=1.2,
    )

    # Create display with aggressive retry
    spi = create_retry_spi_interface(retry_policy=aggressive_policy)
    with EPaperDisplay(vcom=-2.0, spi_interface=spi) as display:
        width, height = display.init()

        # Create a series of images with increasing complexity
        complexities = [
            ("Simple", 100),
            ("Medium", 500),
            ("Complex", 1000),
        ]

        for name, noise_points in complexities:
            logger.info(f"\nDisplaying {name} pattern...")

            # Create pattern with varying complexity
            img = Image.new("L", (300, 200), 255)
            draw = ImageDraw.Draw(img)

            # Add complexity
            pixels = img.load()
            if pixels:
                for _ in range(noise_points):
                    x = random.randint(0, 299)  # noqa: S311
                    y = random.randint(0, 199)  # noqa: S311
                    pixels[x, y] = random.randint(0, 255)  # noqa: S311

            # Draw label
            draw.text(
                (150, 100),
                f"{name} ({noise_points} points)",
                fill=0,
                anchor="mm",
            )

            # Display with retries
            display.display_partial(
                img,
                x=(width - 300) // 2,
                y=(height - 200) // 2,
                mode=DisplayMode.DU,  # Fast mode more prone to errors
            )

            logger.info(f"{name} pattern displayed successfully")


def demonstrate_custom_retry_handling() -> None:
    """Demonstrate custom retry handling for specific scenarios."""
    logger.info("\n=== Custom Retry Handling Demo ===")

    # Create a display with standard retry policy
    standard_policy = RetryPolicy()
    spi = create_retry_spi_interface(retry_policy=standard_policy)
    with EPaperDisplay(vcom=-2.0, spi_interface=spi) as display:
        width, height = display.init()

        # Demonstrate different display modes with retry
        modes = [
            (DisplayMode.GC16, "Full refresh (most reliable)"),
            (DisplayMode.DU, "Fast update (may need retries)"),
            (DisplayMode.A2, "Binary mode (sensitive to noise)"),
        ]

        for mode, description in modes:
            logger.info(f"\nTesting {description}...")

            # Create appropriate test image
            img = Image.new("L", (200, 100), 255)
            draw = ImageDraw.Draw(img)
            draw.text(
                (100, 50),
                mode.name,
                fill=0,
                anchor="mm",
            )

            # Display with mode-specific handling
            try:
                display.display_partial(
                    img,
                    x=(width - 200) // 2,
                    y=(height - 100) // 2,
                    mode=mode,
                )
                logger.info(f"{mode.name} completed successfully")
            except Exception as e:
                logger.error(f"{mode.name} failed after retries: {e}")


def main() -> None:
    """Run all retry demonstrations."""
    logger.info("Starting IT8951 Retry Mechanism Demo")
    logger.info("This demo shows how retry policies help handle transient failures")

    # Run demonstrations
    demonstrate_basic_retry()
    demonstrate_progressive_retry()
    demonstrate_custom_retry_handling()

    logger.info("\nRetry demo completed!")
    logger.info("The retry mechanism helps ensure reliable communication")
    logger.info("even in electrically noisy environments or with timing issues.")


if __name__ == "__main__":
    main()
