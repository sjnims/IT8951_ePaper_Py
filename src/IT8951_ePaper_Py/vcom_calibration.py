"""VCOM calibration utilities for IT8951 e-paper driver.

This module provides utilities for interactive VCOM voltage calibration.
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image


class VCOMAction(Enum):
    """User actions during VCOM calibration."""

    NEXT = "next"
    SELECT = "select"
    BACK = "back"
    QUIT = "quit"


@dataclass
class VCOMCalibrationSession:
    """State container for VCOM calibration session."""

    start_voltage: float
    end_voltage: float
    step: float
    current_voltage: float
    previous_voltage: float | None = None

    def can_go_back(self) -> bool:
        """Check if we can go back to previous voltage."""
        return self.previous_voltage is not None

    def at_end(self) -> bool:
        """Check if we've reached the end of the range."""
        return self.current_voltage >= self.end_voltage

    def advance(self) -> bool:
        """Advance to next voltage. Returns True if successful."""
        if self.at_end():
            return False

        self.previous_voltage = self.current_voltage
        self.current_voltage = min(self.current_voltage + self.step, self.end_voltage)
        return True

    def go_back(self) -> bool:
        """Go back to previous voltage. Returns True if successful."""
        if not self.can_go_back() or self.previous_voltage is None:
            return False

        # Swap current and previous
        self.current_voltage, self.previous_voltage = self.previous_voltage, self.current_voltage
        return True


def parse_user_action(user_input: str) -> VCOMAction:
    """Parse user input into a VCOM action.

    Args:
        user_input: Raw user input string.

    Returns:
        VCOMAction corresponding to the input.
    """
    action = user_input.strip().lower()

    if action == "select":
        return VCOMAction.SELECT
    if action == "back":
        return VCOMAction.BACK
    if action == "quit":
        return VCOMAction.QUIT
    # Default to NEXT for empty input or anything else
    return VCOMAction.NEXT


def print_calibration_header(session: VCOMCalibrationSession) -> None:
    """Print calibration session header."""
    print("\nVCOM Calibration Helper")
    print("======================")
    print(
        f"Testing VCOM range: {session.start_voltage}V to {session.end_voltage}V "
        f"(step: {session.step}V)"
    )
    print("\nInstructions:")
    print("1. Observe the display quality at each voltage")
    print("2. Look for optimal contrast without artifacts")
    print("3. Press Enter to try next voltage")
    print("4. Type 'select' when you find the best voltage")
    print("5. Type 'back' to go to previous voltage")
    print("6. Type 'quit' to cancel\n")


def create_default_test_pattern(width: int, height: int) -> "Image.Image":
    """Create a default test pattern for VCOM calibration.

    Args:
        width: Pattern width in pixels.
        height: Pattern height in pixels.

    Returns:
        Test pattern image with grayscale gradients.
    """
    from PIL import Image, ImageDraw

    test_pattern = Image.new("L", (width, height))
    draw = ImageDraw.Draw(test_pattern)

    # Create grayscale gradient bars
    num_bars = 16
    bar_width = width // num_bars
    for i in range(num_bars):
        gray_value = int(i * 255 / (num_bars - 1))
        x = i * bar_width
        draw.rectangle([x, 0, x + bar_width, height], fill=gray_value)

    # Add crosshairs for alignment
    draw.line([(0, height // 2), (width, height // 2)], fill=0, width=2)
    draw.line([(width // 2, 0), (width // 2, height)], fill=0, width=2)

    return test_pattern
