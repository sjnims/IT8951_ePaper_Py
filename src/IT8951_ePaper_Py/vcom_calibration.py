"""VCOM calibration utilities for IT8951 e-paper driver.

This module provides utilities for interactive VCOM voltage calibration,
helping users find the optimal VCOM voltage for their e-paper display.

VCOM (Common Voltage) is a critical parameter that affects display quality:
- Too high (less negative): Poor contrast, faded images
- Too low (more negative): Ghosting, image retention
- Just right: Clear images with good contrast and minimal ghosting

The calibration process involves:
1. Testing different voltages within a safe range
2. Displaying test patterns at each voltage
3. Visually selecting the voltage with best image quality
4. Storing the optimal value for future use

Typical VCOM ranges:
- Most panels: -1.5V to -2.5V
- Default starting point: -2.0V
- Step size: 0.05V to 0.1V for fine tuning
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    pass  # Additional type-checking only imports can go here


class VCOMAction(Enum):
    """User actions during VCOM calibration.

    Defines the possible user inputs during the interactive calibration
    process. These actions control navigation through voltage values.

    Values:
        NEXT: Advance to the next voltage in the test range.
        SELECT: Choose the current voltage as optimal.
        BACK: Return to the previous voltage.
        QUIT: Cancel calibration without selecting a voltage.
    """

    NEXT = "next"
    SELECT = "select"
    BACK = "back"
    QUIT = "quit"


@dataclass
class VCOMCalibrationSession:
    """State container for VCOM calibration session.

    Manages the state of an interactive VCOM calibration session,
    tracking the voltage range being tested and navigation history.

    Attributes:
        start_voltage: Beginning of the voltage test range (most negative).
        end_voltage: End of the voltage test range (least negative).
        step: Voltage increment between test values.
        current_voltage: Currently displayed test voltage.
        previous_voltage: Last tested voltage for back navigation.
            None if at the start of the session.

    Example:
        >>> session = VCOMCalibrationSession(
        ...     start_voltage=-2.5,
        ...     end_voltage=-1.5,
        ...     step=0.1,
        ...     current_voltage=-2.5
        ... )
        >>> session.advance()
        True
        >>> session.current_voltage
        -2.4
    """

    start_voltage: float
    end_voltage: float
    step: float
    current_voltage: float
    previous_voltage: float | None = None

    def can_go_back(self) -> bool:
        """Check if we can go back to previous voltage.

        Returns:
            True if a previous voltage exists to return to,
            False if at the beginning of the session.
        """
        return self.previous_voltage is not None

    def at_end(self) -> bool:
        """Check if we've reached the end of the range.

        Returns:
            True if the current voltage equals or exceeds the end voltage,
            False if more voltages remain to test.
        """
        return self.current_voltage >= self.end_voltage

    def advance(self) -> bool:
        """Advance to next voltage in the test range.

        Moves to the next voltage by adding the step value, ensuring
        we don't exceed the end voltage. Updates navigation history.

        Returns:
            True if successfully advanced to a new voltage,
            False if already at the end of the range.

        Example:
            >>> session.current_voltage
            -2.0
            >>> session.advance()
            True
            >>> session.current_voltage
            -1.9
            >>> session.previous_voltage
            -2.0
        """
        if self.at_end():
            return False

        self.previous_voltage = self.current_voltage
        self.current_voltage = min(self.current_voltage + self.step, self.end_voltage)
        return True

    def go_back(self) -> bool:
        """Go back to previous voltage in the test history.

        Returns to the last tested voltage, allowing users to compare
        between adjacent values. The current voltage becomes the new
        previous for potential forward navigation.

        Returns:
            True if successfully moved to previous voltage,
            False if no previous voltage exists.

        Example:
            >>> session.current_voltage
            -1.9
            >>> session.previous_voltage
            -2.0
            >>> session.go_back()
            True
            >>> session.current_voltage
            -2.0
            >>> session.previous_voltage
            -1.9
        """
        if not self.can_go_back() or self.previous_voltage is None:
            return False

        # Swap current and previous
        self.current_voltage, self.previous_voltage = self.previous_voltage, self.current_voltage
        return True


def parse_user_action(user_input: str) -> VCOMAction:
    """Parse user input into a VCOM action.

    Converts user text input into standardized action enums for the
    calibration state machine. Case-insensitive and whitespace-tolerant.

    Args:
        user_input: Raw user input string from keyboard.

    Returns:
        VCOMAction enum value corresponding to the input.
        Defaults to NEXT for empty input or unrecognized commands.

    Examples:
        >>> parse_user_action("")  # Press Enter
        <VCOMAction.NEXT: 'next'>
        >>> parse_user_action("select")
        <VCOMAction.SELECT: 'select'>
        >>> parse_user_action("BACK  ")
        <VCOMAction.BACK: 'back'>
        >>> parse_user_action("unknown")
        <VCOMAction.NEXT: 'next'>
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
    """Print calibration session header with instructions.

    Displays a user-friendly header explaining the calibration process
    and available commands. Should be called once at the start of
    calibration.

    Args:
        session: Current calibration session containing voltage range info.

    Example Output:
        VCOM Calibration Helper
        ======================
        Testing VCOM range: -2.5V to -1.5V (step: 0.1V)

        Instructions:
        1. Observe the display quality at each voltage
        2. Look for optimal contrast without artifacts
        3. Press Enter to try next voltage
        4. Type 'select' when you find the best voltage
        5. Type 'back' to go to previous voltage
        6. Type 'quit' to cancel
    """
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


def create_default_test_pattern(width: int, height: int) -> Image.Image:
    """Create a default test pattern for VCOM calibration.

    Generates a comprehensive test pattern designed to reveal VCOM-related
    display issues. The pattern includes grayscale gradients and alignment
    markers to help identify optimal voltage settings.

    Args:
        width: Pattern width in pixels. Should match display width.
        height: Pattern height in pixels. Should match display height.

    Returns:
        PIL Image in grayscale mode ('L') containing:
        - 16 vertical grayscale bars from black to white
        - Crosshairs for alignment and ghosting detection

    Example:
        >>> pattern = create_default_test_pattern(800, 600)
        >>> pattern.mode
        'L'
        >>> pattern.size
        (800, 600)

    Note:
        The grayscale gradient helps identify:
        - Contrast issues (bars not distinct)
        - Ghosting (previous images visible)
        - Uneven voltage distribution (bars appear wavy)

        Crosshairs help detect:
        - Edge bleeding or spreading
        - Alignment problems
    """
    from PIL import ImageDraw

    test_pattern = Image.new("L", (width, height))
    draw = ImageDraw.Draw(test_pattern)

    # Create grayscale gradient bars - 16 levels from black to white
    num_bars = 16
    bar_width = width // num_bars
    for i in range(num_bars):
        # Calculate gray value: 0 (black) to 255 (white)
        gray_value = int(i * 255 / (num_bars - 1))
        x = i * bar_width
        draw.rectangle([x, 0, x + bar_width, height], fill=gray_value)

    # Add crosshairs for alignment and edge quality testing
    # Horizontal line at center
    draw.line([(0, height // 2), (width, height // 2)], fill=0, width=2)
    # Vertical line at center
    draw.line([(width // 2, 0), (width // 2, height)], fill=0, width=2)

    return test_pattern
