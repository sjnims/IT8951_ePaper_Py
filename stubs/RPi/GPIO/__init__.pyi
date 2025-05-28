"""Type stubs for RPi.GPIO module."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

# Pin numbering modes
BCM: int
BOARD: int

# Pin modes
IN: int
OUT: int

# Pull up/down resistors
PUD_OFF: int
PUD_DOWN: int
PUD_UP: int

# Edge detection
RISING: int
FALLING: int
BOTH: int

# Pin states
HIGH: int
LOW: int

# Version info
VERSION: str
RPI_INFO: dict[str, str | int]

def setmode(mode: int) -> None:
    """Set the GPIO pin numbering mode."""
    ...

def setwarnings(flag: bool) -> None:
    """Enable/disable warning messages."""
    ...

def setup(
    channel: int | list[int], direction: int, pull_up_down: int = 20, initial: int = -1
) -> None:
    """Setup a GPIO channel or list of channels."""
    ...

def output(channel: int | list[int], state: int | bool | list[int] | list[bool]) -> None:
    """Output to a GPIO channel or list of channels."""
    ...

def input(channel: int) -> int:  # noqa: A001
    """Read the value of a GPIO pin."""
    ...

def cleanup(channel: int | list[int] | None = None) -> None:
    """Clean up GPIO channels."""
    ...

def add_event_detect(
    channel: int, edge: int, callback: Callable[[int], None] | None = None, bouncetime: int = 0
) -> None:
    """Add edge detection to a GPIO channel."""
    ...

def remove_event_detect(channel: int) -> None:
    """Remove edge detection from a GPIO channel."""
    ...

def event_detected(channel: int) -> bool:
    """Check if an edge was detected on a GPIO channel."""
    ...

def add_event_callback(channel: int, callback: Callable[[int], None]) -> None:
    """Add a callback function to a GPIO channel."""
    ...

def wait_for_edge(channel: int, edge: int, bouncetime: int = 0, timeout: int = -1) -> int | None:
    """Wait for an edge on a GPIO channel."""
    ...

def gpio_function(channel: int) -> int:
    """Return the current GPIO function (IN, OUT, PWM, SERIAL, I2C, SPI)."""
    ...

def getmode() -> int | None:
    """Get the current GPIO pin numbering mode."""
    ...

class PWM:
    """Pulse Width Modulation class."""

    def __init__(self, channel: int, frequency: float) -> None:
        """Initialize PWM on a channel at a specific frequency."""
        ...
    def start(self, dutycycle: float) -> None:
        """Start PWM output."""
        ...
    def stop(self) -> None:
        """Stop PWM output."""
        ...
    def ChangeDutyCycle(self, dutycycle: float) -> None:  # noqa: N802
        """Change the duty cycle."""
        ...
    def ChangeFrequency(self, frequency: float) -> None:  # noqa: N802
        """Change the frequency."""
        ...
