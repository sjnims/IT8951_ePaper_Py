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
from typing import ClassVar


class SystemCommand(IntEnum):
    """System control commands."""

    SYS_RUN = 0x0001
    STANDBY = 0x0002
    SLEEP = 0x0003
    REG_RD = 0x0010
    REG_WR = 0x0011
    MEM_BST_WR = 0x0014
    LD_IMG = 0x0020
    LD_IMG_AREA = 0x0021
    LD_IMG_END = 0x0022


class UserCommand(IntEnum):
    """User-defined commands."""

    DPY_AREA = 0x0034
    GET_DEV_INFO = 0x0302
    DPY_BUF_AREA = 0x0037
    VCOM = 0x0039


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
    """Display update modes."""

    INIT = 0
    DU = 1
    GC16 = 2
    GL16 = 3
    A2 = 4
    GLR16 = 5  # Ghost reduction 16-level (scheduled for v0.6.0)
    GLD16 = 6  # Ghost level detection 16 (scheduled for v0.6.0)
    DU4 = 7  # Direct update 4-level (scheduled for v0.6.0)


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

    PREAMBLE_READ = 0x1000
    PREAMBLE_CMD = 0x6000
    PREAMBLE_DATA = 0x0000
    DUMMY_DATA = 0x0000
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

    RESET = 17
    BUSY = 24
    CS = 8  # Chip select (handled by spidev, kept for reference)


class DisplayConstants:
    """Display-related constants."""

    # DEFAULT_VCOM removed - VCOM must be provided by user
    MIN_VCOM = -5.0
    MAX_VCOM = -0.2
    MAX_WIDTH = 2048
    MAX_HEIGHT = 2048
    DEFAULT_CLEAR_COLOR = 0xFF  # White
    GRAYSCALE_MAX = 255
    PIXEL_ALIGNMENT = 4  # Default alignment for most modes
    PIXEL_ALIGNMENT_1BPP = 32  # 32-bit alignment for 1bpp mode (per wiki)


class MemoryConstants:
    """Memory-related constants."""

    IMAGE_BUFFER_ADDR = 0x001236E0
    IMAGE_BUFFER_ADDR_L = 0x36E0  # Lower 16 bits
    IMAGE_BUFFER_ADDR_H = 0x0012  # Upper 16 bits
    WAVEFORM_ADDR = 0x00886332  # Waveform memory address (not yet used)

    # Memory limits (IT8951 typically has 64MB SDRAM)
    TOTAL_MEMORY_BYTES = 64 * 1024 * 1024  # 64MB
    # Safe threshold: leave room for waveforms and system use
    SAFE_IMAGE_MEMORY_BYTES = 32 * 1024 * 1024  # 32MB for images
    WARNING_THRESHOLD_BYTES = 16 * 1024 * 1024  # Warn at 16MB


class ProtocolConstants:
    """Protocol and communication constants."""

    DEVICE_INFO_SIZE = 20
    PACKED_WRITE_BIT = 0x0001
    VCOM_FACTOR = 1000
    ADDRESS_MASK = 0xFFFF
    MAX_ADDRESS = 0xFFFFFFFF  # 32-bit address space
    BYTE_SHIFT = 8
    BYTE_MASK = 0xFF
    LISAR_HIGH_OFFSET = 2
    LUT_STATE_BIT_POSITION = 7
    LUT_BUSY_BIT = 0x80  # Bit 7 mask for LUT busy state in MISC register
    ENHANCED_DRIVING_VALUE = 0x0602  # Value for ENHANCE_DRIVING register to fix blur
    ADDRESS_SHIFT_16 = 16  # Shift for combining 16-bit address parts

    # Pixel packing bit shifts
    PIXEL_SHIFT_4BPP = 4  # Shift for 4bpp packing
    PIXEL_SHIFT_2BPP_1 = 6  # First pixel shift for 2bpp
    PIXEL_SHIFT_2BPP_2 = 4  # Second pixel shift for 2bpp
    PIXEL_SHIFT_2BPP_3 = 2  # Third pixel shift for 2bpp
    PIXEL_SHIFT_1BPP_THRESHOLD = 128  # Threshold for 1bpp conversion
    PIXEL_SHIFT_1BPP_BITS = 7  # Bit position calculation for 1bpp
    BITS_PER_BYTE = 8  # Number of bits in a byte
    PIXELS_PER_BYTE_1BPP = 8  # Number of pixels packed in one byte for 1bpp
    PIXELS_PER_BYTE_2BPP = 4  # Number of pixels packed in one byte for 2bpp
    PIXELS_PER_BYTE_4BPP = 2  # Number of pixels packed in one byte for 4bpp


class TimingConstants:
    """Timing-related constants."""

    RESET_DURATION_S = 0.1
    BUSY_POLL_FAST_S = 0.001
    BUSY_POLL_SLOW_S = 0.01
    DISPLAY_TIMEOUT_MS = 30000
    DISPLAY_POLL_S = 0.01
