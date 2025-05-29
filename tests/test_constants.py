"""Tests for constants module."""

from IT8951_ePaper_Py.constants import (
    DisplayConstants,
    DisplayMode,
    EndianType,
    GPIOPin,
    MemoryConstants,
    PixelFormat,
    ProtocolConstants,
    Register,
    Rotation,
    RotationAngle,
    SPIConstants,
    SystemCommand,
    TimingConstants,
    UserCommand,
)


class TestConstants:
    """Test constant definitions."""

    def test_system_commands(self) -> None:
        """Test system command values."""
        assert SystemCommand.SYS_RUN == 0x0001
        assert SystemCommand.STANDBY == 0x0002
        assert SystemCommand.SLEEP == 0x0003
        assert SystemCommand.REG_RD == 0x0010
        assert SystemCommand.REG_WR == 0x0011
        assert SystemCommand.LD_IMG == 0x0020
        assert SystemCommand.LD_IMG_AREA == 0x0021
        assert SystemCommand.LD_IMG_END == 0x0022

    def test_user_commands(self) -> None:
        """Test user command values."""
        assert UserCommand.DPY_AREA == 0x0034
        assert UserCommand.GET_DEV_INFO == 0x0302
        assert UserCommand.DPY_BUF_AREA == 0x0037
        assert UserCommand.VCOM == 0x0039

    def test_display_modes(self) -> None:
        """Test display mode values."""
        assert DisplayMode.INIT == 0
        assert DisplayMode.DU == 1
        assert DisplayMode.GC16 == 2
        assert DisplayMode.GL16 == 3
        assert DisplayMode.A2 == 4

    def test_pixel_formats(self) -> None:
        """Test pixel format values."""
        assert PixelFormat.BPP_1 == 0
        assert PixelFormat.BPP_2 == 1
        assert PixelFormat.BPP_4 == 2
        assert PixelFormat.BPP_8 == 3

    def test_rotation_values(self) -> None:
        """Test rotation values."""
        assert Rotation.ROTATE_0 == 0
        assert Rotation.ROTATE_90 == 1
        assert Rotation.ROTATE_180 == 2
        assert Rotation.ROTATE_270 == 3

    def test_endian_types(self) -> None:
        """Test endian type values."""
        assert EndianType.LITTLE == 0
        assert EndianType.BIG == 1

    def test_gpio_pins(self) -> None:
        """Test GPIO pin assignments."""
        assert GPIOPin.RESET == 17
        assert GPIOPin.BUSY == 24
        assert GPIOPin.CS == 8

    def test_spi_constants(self) -> None:
        """Test SPI constants."""
        assert SPIConstants.PREAMBLE_CMD == 0x6000
        assert SPIConstants.PREAMBLE_DATA == 0x0000
        assert SPIConstants.PREAMBLE_READ == 0x1000
        assert SPIConstants.SPI_SPEED_HZ == 12000000
        assert SPIConstants.SPI_MODE == 0
        assert SPIConstants.READ_DUMMY_BYTES == [0x00, 0x00]
        assert SPIConstants.MOCK_DEFAULT_VALUE == 0xFFFF

    def test_display_constants(self) -> None:
        """Test display constants."""
        assert DisplayConstants.DEFAULT_VCOM == -2.0
        assert DisplayConstants.MIN_VCOM == -5.0
        assert DisplayConstants.MAX_VCOM == -0.2
        assert DisplayConstants.MAX_WIDTH == 2048
        assert DisplayConstants.MAX_HEIGHT == 2048
        assert DisplayConstants.TIMEOUT_MS == 30000
        assert DisplayConstants.DEFAULT_CLEAR_COLOR == 0xFF
        assert DisplayConstants.GRAYSCALE_MAX == 255
        assert DisplayConstants.PIXEL_ALIGNMENT == 4

    def test_memory_constants(self) -> None:
        """Test memory constants."""
        assert MemoryConstants.IMAGE_BUFFER_ADDR == 0x001236E0
        assert MemoryConstants.IMAGE_BUFFER_ADDR_L == 0x36E0
        assert MemoryConstants.IMAGE_BUFFER_ADDR_H == 0x0012
        assert MemoryConstants.WAVEFORM_ADDR == 0x00886332
        # Verify that the components combine to form the full address
        assert (
            MemoryConstants.IMAGE_BUFFER_ADDR
            == (MemoryConstants.IMAGE_BUFFER_ADDR_H << 16) | MemoryConstants.IMAGE_BUFFER_ADDR_L
        )

    def test_register_addresses(self) -> None:
        """Test register addresses."""
        assert Register.LISAR == 0x0200
        assert Register.REG_0204 == 0x0204
        assert Register.MISC == 0x1E50
        assert Register.PWR == 0x1E54

    def test_protocol_constants(self) -> None:
        """Test protocol constants."""
        assert ProtocolConstants.DEVICE_INFO_SIZE == 20
        assert ProtocolConstants.PACKED_WRITE_BIT == 0x0001
        assert ProtocolConstants.VCOM_FACTOR == 1000
        assert ProtocolConstants.ADDRESS_MASK == 0xFFFF
        assert ProtocolConstants.MAX_ADDRESS == 0xFFFFFFFF
        assert ProtocolConstants.BYTE_SHIFT == 8
        assert ProtocolConstants.BYTE_MASK == 0xFF
        assert ProtocolConstants.LISAR_HIGH_OFFSET == 2
        assert ProtocolConstants.LUT_STATE_BIT_POSITION == 7

    def test_timing_constants(self) -> None:
        """Test timing constants."""
        assert TimingConstants.RESET_DURATION_S == 0.1
        assert TimingConstants.BUSY_POLL_FAST_S == 0.001
        assert TimingConstants.BUSY_POLL_SLOW_S == 0.01
        assert TimingConstants.DISPLAY_TIMEOUT_MS == 30000
        assert TimingConstants.DISPLAY_POLL_S == 0.01

    def test_rotation_angle_constants(self) -> None:
        """Test rotation angle constants."""
        assert RotationAngle.ANGLE_90 == -90
        assert RotationAngle.ANGLE_180 == 180
        assert RotationAngle.ANGLE_270 == 90
