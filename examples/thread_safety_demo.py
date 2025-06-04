#!/usr/bin/env python3
"""Demonstrate thread-safe usage of the IT8951 e-paper display.

This example shows how to use the ThreadSafeEPaperDisplay wrapper to safely
access the display from multiple threads concurrently.
"""

import logging
import random
import threading
import time

from PIL import Image, ImageDraw, ImageFont

from IT8951_ePaper_Py import ThreadSafeEPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode

# Configure logging to see thread activity
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)-10s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_test_image(width: int, height: int, text: str) -> Image.Image:
    """Create a test image with text and timestamp."""
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    # Try to use a better font if available
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    except Exception:
        font = ImageFont.load_default()

    # Draw text
    text_with_time = f"{text}\n{time.strftime('%H:%M:%S')}"
    draw.multiline_text(
        (width // 2, height // 2),
        text_with_time,
        fill=0,
        font=font,
        anchor="mm",
        align="center",
    )

    # Draw a border
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline=0, width=3)

    return img


def display_worker(
    display: ThreadSafeEPaperDisplay,
    worker_id: int,
    region: tuple[int, int, int, int],
    iterations: int = 3,
) -> None:
    """Worker thread that updates a specific region of the display."""
    logger.info(f"Worker {worker_id} starting")

    region_x, region_y, region_width, region_height = region

    for i in range(iterations):
        # Create an image for this worker
        img = create_test_image(
            region_width,
            region_height,
            f"Worker {worker_id}\nUpdate {i + 1}",
        )

        # Random sleep to simulate work (not cryptographic)
        time.sleep(random.uniform(0.1, 0.5))  # noqa: S311

        # Update the display region
        logger.info(f"Worker {worker_id} updating region ({region_x}, {region_y})")
        display.display_partial(
            img,
            x=region_x,
            y=region_y,
            mode=DisplayMode.DU,  # Fast update mode
        )

        # Random sleep between updates (not cryptographic)
        time.sleep(random.uniform(0.5, 1.0))  # noqa: S311

    logger.info(f"Worker {worker_id} finished")


def status_monitor(display: ThreadSafeEPaperDisplay, duration: float) -> None:
    """Monitor thread that periodically checks display status."""
    logger.info("Status monitor starting")
    start_time = time.time()

    while time.time() - start_time < duration:
        # Get device status
        status = display.get_device_status()
        logger.info(
            f"Display status - Power: {status['power_state']}, VCOM: {status['vcom_voltage']}V"
        )

        # Check auto-sleep
        display.check_auto_sleep()

        time.sleep(2.0)

    logger.info("Status monitor finished")


def power_manager(display: ThreadSafeEPaperDisplay, duration: float) -> None:
    """Power management thread that demonstrates sleep/wake cycles."""
    logger.info("Power manager starting")
    start_time = time.time()

    while time.time() - start_time < duration:
        time.sleep(5.0)

        # Enter standby mode
        logger.info("Entering standby mode")
        display.standby()

        time.sleep(2.0)

        # Wake up
        logger.info("Waking from standby")
        display.wake()

        time.sleep(3.0)

    logger.info("Power manager finished")


def main() -> None:
    """Main demonstration of thread-safe display usage."""
    # Create thread-safe display instance
    logger.info("Creating thread-safe display")
    display = ThreadSafeEPaperDisplay(vcom=-2.0)

    try:
        # Initialize display
        width, height = display.init()
        logger.info(f"Display initialized: {width}x{height}")

        # Clear display
        logger.info("Clearing display")
        display.clear()

        # Set auto-sleep timeout
        display.set_auto_sleep_timeout(30.0)

        # Define regions for workers (divide display into quadrants)
        regions = [
            (0, 0, width // 2, height // 2),  # Top-left
            (width // 2, 0, width // 2, height // 2),  # Top-right
            (0, height // 2, width // 2, height // 2),  # Bottom-left
            (width // 2, height // 2, width // 2, height // 2),  # Bottom-right
        ]

        # Create worker threads
        workers = []
        for i, region in enumerate(regions):
            worker = threading.Thread(
                target=display_worker,
                args=(display, i + 1, region),
                name=f"Worker-{i + 1}",
            )
            workers.append(worker)

        # Create monitor threads
        status_thread = threading.Thread(
            target=status_monitor,
            args=(display, 15.0),  # Run for 15 seconds
            name="StatusMonitor",
        )

        power_thread = threading.Thread(
            target=power_manager,
            args=(display, 15.0),  # Run for 15 seconds
            name="PowerManager",
        )

        # Start all threads
        logger.info("Starting all threads")
        for worker in workers:
            worker.start()
        status_thread.start()
        power_thread.start()

        # Wait for all threads to complete
        logger.info("Waiting for threads to complete")
        for worker in workers:
            worker.join()
        status_thread.join()
        power_thread.join()

        # Final status check
        logger.info("All threads completed")
        status = display.get_device_status()
        logger.info(f"Final display status: {status}")

        # Clear display at the end
        logger.info("Final clear")
        display.clear()

    finally:
        # Clean up
        display.close()
        logger.info("Display closed")


if __name__ == "__main__":
    main()
