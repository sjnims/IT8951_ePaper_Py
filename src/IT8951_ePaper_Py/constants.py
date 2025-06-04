"""Constants and configuration for IT8951 e-paper driver.

This module contains all hardware constants, command definitions, and
configuration values for the IT8951 e-paper controller. Constants are
organized into logical groups using IntEnum and dataclasses.

Constant Categories:
    - SystemCommand: Low-level system control commands
    - UserCommand: High-level user commands
    - DisplayMode: Display refresh modes (speed vs quality tradeoffs)
    - PixelFormat: Supported pixel bit depths
    - Rotation: Image rotation options
    - EndianType: Byte order options
    - Register: Hardware register addresses
    - Various configuration constants for GPIO, SPI, timing, etc.
"""

from enum import IntEnum
from typing import ClassVar, TypedDict


class ModeInfoRequired(TypedDict):
    """Required fields for display mode information."""
    
    name: str
    grayscale_levels: int
    speed: str
    quality: str
    use_case: str
    ghosting: str
    recommended_bpp: list[int]


class ModeInfo(ModeInfoRequired, total=False):
    """Display mode information with optional fields."""
    
    description: str
    hardware_requirements: str | None
    hardware_support: str
    warning: str


class SystemCommand(IntEnum):
    """System control commands."""

    SYS_RUN = 0x0001  # Activate the system from standby/sleep
    STANDBY = 0x0002  # Enter standby mode (quick wake, moderate power)
    SLEEP = 0x0003  # Enter sleep mode (slow wake, lowest power)
    REG_RD = 0x0010  # Read from a register
    REG_WR = 0x0011  # Write to a register
    MEM_BST_WR = 0x0014  # Memory burst write for fast data transfer
    LD_IMG = 0x0020  # Load image to display buffer
    LD_IMG_AREA = 0x0021  # Load image to specific area
    LD_IMG_END = 0x0022  # End image loading operation


class UserCommand(IntEnum):
    """User-defined commands."""

    DPY_AREA = 0x0034  # Display an area with specified mode
    GET_DEV_INFO = 0x0302  # Get device information (model, resolution, etc.)
    DPY_BUF_AREA = 0x0037  # Display from specific buffer address
    VCOM = 0x0039  # Set VCOM voltage


class Register(IntEnum):
    """IT8951 registers.

    Key registers for IT8951 control and status monitoring:
    - LISAR: Load Image Start Address Register (target memory address)
    - REG_0204: Configuration register (packed write mode control)
    - MISC: Miscellaneous status register (LUT busy state)
    - PWR: Power control register (standby/sleep modes)
    - MCSR: Memory Controller Status Register
    """

    LISAR = 0x0200  # Load Image Start Address Register (16-bit low)
    REG_0204 = 0x0204  # Configuration register (bit 0: packed write enable)
    ENHANCE_DRIVING = 0x0038  # Enhanced driving capability register (0x0602 for blur fix)
    MISC = 0x1E50  # Miscellaneous register (bit 7: LUT busy)
    PWR = 0x1E54  # Power register (for power management features)
    MCSR = 0x18004  # Memory controller status register


class DisplayMode(IntEnum):
    """Display update modes.

    The IT8951 controller supports various display modes optimized for different
    use cases. Each mode offers different trade-offs between speed, quality, and
    ghosting reduction.
    """

    INIT = 0  # Initialize display (full refresh, clears ghosting)
    DU = 1  # Direct Update (fast, 2-level, may show artifacts)
    GC16 = 2  # Grayscale Clear 16 (high quality, 16-level, slower)
    GL16 = 3  # Grayscale Light 16 (faster than GC16, slight quality reduction)
    A2 = 4  # Animation mode (very fast, 2-level, for rapid updates)
    GLR16 = 5  # Ghost reduction 16-level (v0.7.0 - reduces ghosting artifacts)
    GLD16 = 6  # Ghost level detection 16 (v0.7.0 - adaptive ghost compensation)
    DU4 = 7  # Direct update 4-level (v0.7.0 - fast 4-grayscale mode)


class DisplayModeCharacteristics:
    """Characteristics of each display mode for validation and optimization."""

    MODE_INFO: ClassVar[dict[DisplayMode, ModeInfo]] = {
        DisplayMode.INIT: {
            "name": "INIT",
            "grayscale_levels": 1,
            "speed": "slow",
            "quality": "N/A",
            "use_case": "Clear display, remove ghosting",
            "ghosting": "removes",
            "recommended_bpp": [0, 1, 2, 3],  # All formats supported
        },
        DisplayMode.DU: {
            "name": "DU",
            "grayscale_levels": 2,
            "speed": "fast",
            "quality": "low",
            "use_case": "Text, simple graphics",
            "ghosting": "high",
            "recommended_bpp": [0, 1],  # Best with 1bpp or 2bpp
        },
        DisplayMode.GC16: {
            "name": "GC16",
            "grayscale_levels": 16,
            "speed": "slowest",
            "quality": "highest",
            "use_case": "Photos, detailed images",
            "ghosting": "low",
            "recommended_bpp": [2, 3],  # Best with 4bpp or 8bpp
        },
        DisplayMode.GL16: {
            "name": "GL16",
            "grayscale_levels": 16,
            "speed": "medium",
            "quality": "high",
            "use_case": "General purpose",
            "ghosting": "medium",
            "recommended_bpp": [2, 3],  # Best with 4bpp or 8bpp
        },
        DisplayMode.A2: {
            "name": "A2",
            "grayscale_levels": 2,
            "speed": "fastest",
            "quality": "lowest",
            "use_case": "Animations, rapid updates",
            "ghosting": "very high",
            "recommended_bpp": [0],  # Best with 1bpp
            "warning": "Use INIT mode periodically to clear ghosting",
        },
        DisplayMode.GLR16: {
            "name": "GLR16",
            "grayscale_levels": 16,
            "speed": "slow",
            "quality": "high",
            "use_case": "When ghosting reduction is critical",
            "ghosting": "very low",
            "recommended_bpp": [2, 3],  # Best with 4bpp or 8bpp
            "hardware_support": "varies",
        },
        DisplayMode.GLD16: {
            "name": "GLD16",
            "grayscale_levels": 16,
            "speed": "slow",
            "quality": "high",
            "use_case": "Adaptive ghosting compensation",
            "ghosting": "adaptive",
            "recommended_bpp": [2, 3],  # Best with 4bpp or 8bpp
            "hardware_support": "varies",
        },
        DisplayMode.DU4: {
            "name": "DU4",
            "grayscale_levels": 4,
            "speed": "fast",
            "quality": "medium",
            "use_case": "Simple graphics with some shading",
            "ghosting": "medium-high",
            "recommended_bpp": [1, 2],  # Best with 2bpp or 4bpp
            "hardware_support": "varies",
        },
    }


class PixelFormat(IntEnum):
    """Pixel format options."""

    BPP_1 = 0  # 1 bit per pixel (for binary images, requires 32-bit alignment)
    BPP_2 = 1  # 2 bits per pixel (4 gray levels)
    BPP_4 = 2  # 4 bits per pixel (16 gray levels, default, recommended by Waveshare)
    BPP_8 = 3  # 8 bits per pixel (256 gray levels)


class Rotation(IntEnum):
    """Image rotation options."""

    ROTATE_0 = 0
    ROTATE_90 = 1
    ROTATE_180 = 2
    ROTATE_270 = 3


class RotationAngle:
    """Rotation angles in degrees for PIL operations."""

    ANGLE_90 = -90
    ANGLE_180 = 180
    ANGLE_270 = 90


class EndianType(IntEnum):
    """Endian type for image loading."""

    LITTLE = 0


class PowerState(IntEnum):
    """Power state of the IT8951 controller."""

    ACTIVE = 0
    STANDBY = 1
    SLEEP = 2


class SPIConstants:
    """SPI communication constants."""

    PREAMBLE_READ = 0x1000  # Preamble for read operations
    PREAMBLE_CMD = 0x6000  # Preamble for command operations
    PREAMBLE_DATA = 0x0000  # Preamble for data operations
    DUMMY_DATA = 0x0000  # Dummy data for read operations
    # Pi-specific speeds based on core clock dividers (Waveshare recommendations)
    # Pi 3: 400MHz core / 16 = 25MHz (but we use conservative 15.625MHz based on 250MHz/16)
    # Pi 4: More conservative divider for stability
    SPI_SPEED_PI3_HZ = 15625000  # 250MHz / 16 = 15.625MHz
    SPI_SPEED_PI4_HZ = 7812500  # 250MHz / 32 = 7.8125MHz
    SPI_MODE = 0
    READ_DUMMY_BYTES: ClassVar[list[int]] = [0x00, 0x00]
    MOCK_DEFAULT_VALUE = 0xFFFF


class GPIOPin:
    """GPIO pin assignments for Raspberry Pi."""

    RESET = 17  # GPIO pin for hardware reset (BCM numbering)
    BUSY = 24  # GPIO pin for busy signal (BCM numbering)
    CS = 8  # Chip select (handled by spidev, kept for reference)


class DisplayConstants:
    """Display-related constants."""

    # DEFAULT_VCOM removed - VCOM must be provided by user
    MIN_VCOM = -5.0  # Minimum safe VCOM voltage
    MAX_VCOM = -0.2  # Maximum safe VCOM voltage
    MAX_WIDTH = 2048  # Maximum supported display width
    MAX_HEIGHT = 2048  # Maximum supported display height
    DEFAULT_CLEAR_COLOR = 0xFF  # White (for clear operations)
    GRAYSCALE_MAX = 255  # Maximum grayscale value (8-bit)
    VCOM_TOLERANCE = 0.05  # Voltage tolerance for VCOM verification (in volts)
    PIXEL_ALIGNMENT = 4  # Default alignment for most modes
    PIXEL_ALIGNMENT_1BPP = 32  # 32-bit alignment for 1bpp mode (per wiki)


class PerformanceConstants:
    """Performance optimization thresholds."""

    NUMPY_OPTIMIZATION_THRESHOLD = 10000  # Pixel count threshold for numpy optimization


class MemoryConstants:
    """Memory-related constants."""

    IMAGE_BUFFER_ADDR = 0x001236E0  # Default image buffer start address
    IMAGE_BUFFER_ADDR_L = 0x36E0  # Lower 16 bits of buffer address
    IMAGE_BUFFER_ADDR_H = 0x0012  # Upper 16 bits of buffer address
    WAVEFORM_ADDR = 0x00886332  # Waveform memory address (not yet used)

    # Memory limits (IT8951 typically has 64MB SDRAM)
    TOTAL_MEMORY_BYTES = 64 * 1024 * 1024  # 64MB
    # Safe threshold: leave room for waveforms and system use
    SAFE_IMAGE_MEMORY_BYTES = 32 * 1024 * 1024  # 32MB for images
    WARNING_THRESHOLD_BYTES = 16 * 1024 * 1024  # Warn at 16MB


class ProtocolConstants:
    """Protocol and communication constants."""

    DEVICE_INFO_SIZE = 20  # Size of device info structure in words
    PACKED_WRITE_BIT = 0x0001  # Bit to enable packed write mode
    VCOM_FACTOR = 1000  # Conversion factor for VCOM (V to mV)
    ADDRESS_MASK = 0xFFFF  # Mask for 16-bit address parts
    MAX_ADDRESS = 0xFFFFFFFF  # Maximum 32-bit address
    BYTE_SHIFT = 8  # Bits to shift for byte operations
    BYTE_MASK = 0xFF  # Mask for single byte
    LISAR_HIGH_OFFSET = 2  # Offset to high address register
    LUT_STATE_BIT_POSITION = 7  # Position of LUT busy bit
    LUT_BUSY_BIT = 0x80  # Bit 7 mask for LUT busy state
    ENHANCED_DRIVING_VALUE = 0x0602  # Value to fix blur issues
    ADDRESS_SHIFT_16 = 16  # Shift for 16-bit address combination

    # Pixel packing bit shifts
    PIXEL_SHIFT_4BPP = 4  # Right shift to reduce 8-bit to 4-bit
    PIXEL_SHIFT_2BPP_1 = 6  # First pixel position in 2bpp byte
    PIXEL_SHIFT_2BPP_2 = 4  # Second pixel position in 2bpp byte
    PIXEL_SHIFT_2BPP_3 = 2  # Third pixel position in 2bpp byte
    PIXEL_SHIFT_1BPP_THRESHOLD = 128  # Black/white threshold for 1bpp
    PIXEL_SHIFT_1BPP_BITS = 7  # MSB position for 1bpp packing
    BITS_PER_BYTE = 8  # Standard byte size
    PIXELS_PER_BYTE_1BPP = 8  # 8 pixels per byte in 1bpp mode
    PIXELS_PER_BYTE_2BPP = 4  # 4 pixels per byte in 2bpp mode
    PIXELS_PER_BYTE_4BPP = 2  # 2 pixels per byte in 4bpp mode


class TimingConstants:
    """Timing-related constants."""

    RESET_DURATION_S = 0.1  # Hardware reset pulse duration
    BUSY_POLL_FAST_S = 0.001  # Fast polling interval for busy signal
    BUSY_POLL_SLOW_S = 0.01  # Slow polling interval for busy signal
    DISPLAY_TIMEOUT_MS = 30000  # Maximum wait time for display operations (30s)
    DISPLAY_POLL_S = 0.01  # Polling interval for display completion
