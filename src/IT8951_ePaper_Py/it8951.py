"""Core IT8951 e-paper controller driver."""

import time

from IT8951_ePaper_Py.constants import (
    PixelFormat,
    ProtocolConstants,
    Register,
    SystemCommand,
    TimingConstants,
    UserCommand,
)
from IT8951_ePaper_Py.exceptions import (
    DeviceError,
    InitializationError,
    InvalidParameterError,
    IT8951MemoryError,
    IT8951TimeoutError,
)
from IT8951_ePaper_Py.models import (
    AreaImageInfo,
    DeviceInfo,
    DisplayArea,
    LoadImageInfo,
    VCOMConfig,
)
from IT8951_ePaper_Py.spi_interface import SPIInterface, create_spi_interface


class IT8951:
    """IT8951 e-paper controller driver."""

    def __init__(self, spi_interface: SPIInterface | None = None) -> None:
        """Initialize IT8951 driver.

        Args:
            spi_interface: Optional SPI interface. If not provided, will create
                          appropriate interface based on platform.
        """
        self._spi = spi_interface or create_spi_interface()
        self._device_info: DeviceInfo | None = None
        self._initialized = False

    def init(self) -> DeviceInfo:
        """Initialize the IT8951 controller.

        Returns:
            Device information.

        Raises:
            InitializationError: If initialization fails.
        """
        if self._initialized:
            return self._device_info or self._get_device_info()

        try:
            self._spi.init()
            self._system_run()
            self._device_info = self._get_device_info()
            self._enable_packed_write()
            self._initialized = True
            return self._device_info
        except Exception as e:
            self.close()
            raise InitializationError(f"Failed to initialize IT8951: {e}") from e

    def close(self) -> None:
        """Close the driver and cleanup resources."""
        if self._spi:
            self._spi.close()
        self._initialized = False
        self._device_info = None

    def _system_run(self) -> None:
        """Send system run command."""
        self._spi.write_command(SystemCommand.SYS_RUN)

    def _get_device_info(self) -> DeviceInfo:
        """Get device information from controller.

        Returns:
            Device information.
        """
        self._spi.write_command(UserCommand.GET_DEV_INFO)
        data = self._spi.read_data_bulk(ProtocolConstants.DEVICE_INFO_SIZE)

        fw_version: list[int] = []
        lut_version: list[int] = []

        for i in range(8):
            fw_version.append(data[i + 4])
            lut_version.append(data[i + 12])

        return DeviceInfo(
            panel_width=data[0],
            panel_height=data[1],
            memory_addr_l=data[2],
            memory_addr_h=data[3],
            fw_version=fw_version,
            lut_version=lut_version,
        )

    def _enable_packed_write(self) -> None:
        """Enable packed write mode for better performance."""
        reg_value = self._read_register(Register.REG_0204)
        reg_value |= ProtocolConstants.PACKED_WRITE_BIT
        self._write_register(Register.REG_0204, reg_value)

    def _read_register(self, register: int) -> int:
        """Read a register value.

        Args:
            register: Register address.

        Returns:
            Register value.
        """
        self._spi.write_command(SystemCommand.REG_RD)
        self._spi.write_data(register)
        return self._spi.read_data()

    def _write_register(self, register: int, value: int) -> None:
        """Write a register value.

        Args:
            register: Register address.
            value: Value to write.
        """
        self._spi.write_command(SystemCommand.REG_WR)
        self._spi.write_data(register)
        self._spi.write_data(value)

    def standby(self) -> None:
        """Put device into standby mode."""
        self._ensure_initialized()
        self._spi.write_command(SystemCommand.STANDBY)

    def sleep(self) -> None:
        """Put device into sleep mode."""
        self._ensure_initialized()
        self._spi.write_command(SystemCommand.SLEEP)

    def get_vcom(self) -> float:
        """Get current VCOM voltage.

        Returns:
            VCOM voltage in volts.
        """
        self._ensure_initialized()
        self._spi.write_command(UserCommand.VCOM)
        self._spi.write_data(0)
        vcom_raw = self._spi.read_data()
        return -vcom_raw / ProtocolConstants.VCOM_FACTOR

    def set_vcom(self, voltage: float) -> None:
        """Set VCOM voltage.

        Args:
            voltage: VCOM voltage in volts (must be negative).

        Raises:
            InvalidParameterError: If voltage is out of range.
        """
        self._ensure_initialized()
        try:
            config = VCOMConfig(voltage=voltage)
        except Exception as e:
            raise InvalidParameterError(f"Invalid VCOM voltage: {e}") from e
        vcom_raw = int(-config.voltage * ProtocolConstants.VCOM_FACTOR)
        self._spi.write_command(UserCommand.VCOM)
        self._spi.write_data(1)
        self._spi.write_data(vcom_raw)

    def set_target_memory_addr(self, address: int) -> None:
        """Set target memory address for image loading.

        Args:
            address: Target memory address.

        Raises:
            IT8951MemoryError: If address is invalid.
        """
        self._ensure_initialized()

        # Validate memory address
        if address < 0 or address > ProtocolConstants.MAX_ADDRESS:
            raise IT8951MemoryError(f"Invalid memory address: 0x{address:08X}")

        self._write_register(Register.LISAR, address & ProtocolConstants.ADDRESS_MASK)
        self._write_register(
            Register.LISAR + ProtocolConstants.LISAR_HIGH_OFFSET,
            (address >> (ProtocolConstants.BYTE_SHIFT * 2)) & ProtocolConstants.ADDRESS_MASK,
        )

    def load_image_start(self, info: LoadImageInfo) -> None:
        """Start loading an image to controller memory.

        Args:
            info: Image loading information.
        """
        self._ensure_initialized()
        self.set_target_memory_addr(info.target_memory_addr)

        args = [
            info.endian_type,
            info.pixel_format,
            info.rotate,
            0,
            0,
        ]

        self._spi.write_command(SystemCommand.LD_IMG)
        for arg in args:
            self._spi.write_data(arg)

    def load_image_area_start(self, info: LoadImageInfo, area: AreaImageInfo) -> None:
        """Start loading an image area to controller memory.

        Args:
            info: Image loading information.
            area: Area information.
        """
        self._ensure_initialized()
        self.set_target_memory_addr(info.target_memory_addr)

        args = [
            info.endian_type,
            info.pixel_format,
            info.rotate,
            area.x,
            area.y,
            area.width,
            area.height,
        ]

        self._spi.write_command(SystemCommand.LD_IMG_AREA)
        for arg in args:
            self._spi.write_data(arg)

    def load_image_write(self, data: bytes) -> None:
        """Write image data to controller.

        Args:
            data: Image data bytes.
        """
        self._ensure_initialized()

        words: list[int] = []
        for i in range(0, len(data), 2):
            word = (data[i] << 8) | data[i + 1] if i + 1 < len(data) else data[i] << 8
            words.append(word)

        self._spi.write_command(SystemCommand.MEM_BST_WR)
        self._spi.write_data_bulk(words)

    @staticmethod
    def pack_pixels(pixels: bytes, pixel_format: PixelFormat) -> bytes:
        """Pack pixel data according to the specified format.

        Args:
            pixels: 8-bit pixel data (each byte is one pixel).
            pixel_format: Target pixel format.

        Returns:
            Packed pixel data according to format.

        Raises:
            InvalidParameterError: If pixel format is not supported.
        """
        if pixel_format == PixelFormat.BPP_8:
            # No packing needed for 8bpp
            return pixels
        if pixel_format == PixelFormat.BPP_4:
            # Pack 2 pixels per byte (4 bits each)
            packed: list[int] = []
            for i in range(0, len(pixels), 2):
                # Each pixel is reduced to 4 bits (0-15 range)
                pixel1 = (pixels[i] >> 4) if i < len(pixels) else 0
                pixel2 = (pixels[i + 1] >> 4) if i + 1 < len(pixels) else 0
                # Pack two pixels into one byte (pixel1 in high nibble, pixel2 in low nibble)
                packed_byte = (pixel1 << 4) | pixel2
                packed.append(packed_byte)
            return bytes(packed)
        if pixel_format == PixelFormat.BPP_2:
            # Pack 4 pixels per byte (2 bits each)
            packed: list[int] = []
            for i in range(0, len(pixels), 4):
                # Each pixel is reduced to 2 bits (0-3 range)
                pixel1 = (pixels[i] >> 6) if i < len(pixels) else 0
                pixel2 = (pixels[i + 1] >> 6) if i + 1 < len(pixels) else 0
                pixel3 = (pixels[i + 2] >> 6) if i + 2 < len(pixels) else 0
                pixel4 = (pixels[i + 3] >> 6) if i + 3 < len(pixels) else 0
                # Pack four pixels into one byte
                packed_byte = (pixel1 << 6) | (pixel2 << 4) | (pixel3 << 2) | pixel4
                packed.append(packed_byte)
            return bytes(packed)
        raise InvalidParameterError(f"Pixel format {pixel_format} not yet implemented")

    def load_image_end(self) -> None:
        """End image loading operation."""
        self._ensure_initialized()
        self._spi.write_command(SystemCommand.LD_IMG_END)

    def _validate_display_area(self, area: DisplayArea) -> None:
        """Validate display area bounds.

        Args:
            area: Display area to validate.

        Raises:
            DeviceError: If device info not available.
            InvalidParameterError: If area exceeds panel bounds.
        """
        if not self._device_info:
            raise DeviceError("Device info not available")

        if area.x + area.width > self._device_info.panel_width:
            raise InvalidParameterError("Display area exceeds panel width")
        if area.y + area.height > self._device_info.panel_height:
            raise InvalidParameterError("Display area exceeds panel height")

    def display_area(self, area: DisplayArea, wait: bool = True) -> None:
        """Display an area with specified mode.

        Args:
            area: Display area configuration.
            wait: Whether to wait for display to complete.
        """
        self._ensure_initialized()
        self._validate_display_area(area)

        args = [
            area.x,
            area.y,
            area.width,
            area.height,
            area.mode,
        ]

        self._spi.write_command(UserCommand.DPY_AREA)
        for arg in args:
            self._spi.write_data(arg)

        if wait:
            self._wait_display_ready()

    def display_buffer_area(self, area: DisplayArea, address: int, wait: bool = True) -> None:
        """Display an area from a specific buffer address.

        Args:
            area: Display area configuration.
            address: Buffer memory address.
            wait: Whether to wait for display to complete.
        """
        self._ensure_initialized()
        self._validate_display_area(area)

        args = [
            area.x,
            area.y,
            area.width,
            area.height,
            area.mode,
            address & ProtocolConstants.ADDRESS_MASK,
            (address >> (ProtocolConstants.BYTE_SHIFT * 2)) & ProtocolConstants.ADDRESS_MASK,
        ]

        self._spi.write_command(UserCommand.DPY_BUF_AREA)
        for arg in args:
            self._spi.write_data(arg)

        if wait:
            self._wait_display_ready()

    def _wait_display_ready(self, timeout_ms: int = TimingConstants.DISPLAY_TIMEOUT_MS) -> None:
        """Wait for display operation to complete.

        Args:
            timeout_ms: Timeout in milliseconds.

        Raises:
            IT8951TimeoutError: If timeout occurs.
        """
        start_time = time.time()
        while time.time() - start_time < timeout_ms / 1000:
            lut_state = (
                self._read_register(Register.MISC) >> ProtocolConstants.LUT_STATE_BIT_POSITION
            )
            if lut_state == 0:
                return
            time.sleep(TimingConstants.DISPLAY_POLL_S)

        raise IT8951TimeoutError(f"Display operation timed out after {timeout_ms}ms")

    def _ensure_initialized(self) -> None:
        """Ensure the driver is initialized.

        Raises:
            InitializationError: If not initialized.
        """
        if not self._initialized:
            raise InitializationError("IT8951 not initialized. Call init() first.")

    @property
    def device_info(self) -> DeviceInfo:
        """Get device information.

        Returns:
            Device information.

        Raises:
            InitializationError: If not initialized.
        """
        self._ensure_initialized()
        if not self._device_info:
            raise InitializationError("Device info not available")
        return self._device_info
