"""Constants and configuration for IT8951 e-paper driver."""

from enum import IntEnum


class SystemCommand(IntEnum):
    """System control commands."""

    SYS_RUN = 0x0001
    STANDBY = 0x0002
    SLEEP = 0x0003
    REG_RD = 0x0010
    REG_WR = 0x0011
    MEM_BST_RD_T = 0x0012
    MEM_BST_RD_S = 0x0013
    MEM_BST_WR = 0x0014
    MEM_BST_END = 0x0015
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
    """IT8951 registers."""

    LISAR = 0x0200
    REG_0204 = 0x0204
    REG_0208 = 0x0208
    REG_020A = 0x020A
    REG_020C = 0x020C
    REG_020E = 0x020E
    MISC = 0x1E50
    PWR = 0x1E54
    MCSR = 0x18004


class DisplayMode(IntEnum):
    """Display update modes."""

    INIT = 0
    DU = 1
    GC16 = 2
    GL16 = 3
    A2 = 4
    GLR16 = 5
    GLD16 = 6
    DU4 = 7


class PixelFormat(IntEnum):
    """Pixel format options."""

    BPP_2 = 0
    BPP_3 = 1
    BPP_4 = 2
    BPP_8 = 3


class Rotation(IntEnum):
    """Image rotation options."""

    ROTATE_0 = 0
    ROTATE_90 = 1
    ROTATE_180 = 2
    ROTATE_270 = 3


class EndianType(IntEnum):
    """Endian type for image loading."""

    LITTLE = 0
    BIG = 1


class SPIConstants:
    """SPI communication constants."""

    PREAMBLE_WRITE = 0x0000
    PREAMBLE_READ = 0x1000
    PREAMBLE_CMD = 0x6000
    PREAMBLE_DATA = 0x0000
    DUMMY_DATA = 0x0000
    SPI_SPEED_HZ = 12000000
    SPI_MODE = 0


class GPIOPin:
    """GPIO pin assignments for Raspberry Pi."""

    RESET = 17
    BUSY = 24
    CS = 8


class DisplayConstants:
    """Display-related constants."""

    DEFAULT_VCOM = -2.0
    MIN_VCOM = -5.0
    MAX_VCOM = -0.2
    MAX_WIDTH = 2048
    MAX_HEIGHT = 2048
    TIMEOUT_MS = 5000


class MemoryConstants:
    """Memory-related constants."""

    IMAGE_BUFFER_ADDR = 0x001236E0
    WAVEFORM_ADDR = 0x00886332
