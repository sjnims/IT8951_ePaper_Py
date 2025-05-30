"""High-level display interface for IT8951 e-paper.

This module provides a user-friendly API for controlling e-paper displays
with the IT8951 controller. It handles image loading, format conversion,
and display operations.

Examples:
    Basic usage::

        from IT8951_ePaper_Py import EPaperDisplay

        # Initialize display
        display = EPaperDisplay(vcom=-2.0)
        width, height = display.init()

        # Display an image
        from PIL import Image
        img = Image.open("picture.png")
        display.display_image(img)

        # Clean up
        display.close()
"""

from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

import numpy as np
from PIL import Image

if TYPE_CHECKING:
    from numpy.typing import NDArray

    NumpyArray = NDArray[np.uint8]
else:
    NumpyArray = np.ndarray

from IT8951_ePaper_Py.constants import (
    DisplayConstants,
    DisplayMode,
    MemoryConstants,
    PixelFormat,
    Rotation,
    RotationAngle,
)
from IT8951_ePaper_Py.exceptions import (
    DisplayError,
    InvalidParameterError,
    IT8951MemoryError,
    VCOMError,
)
from IT8951_ePaper_Py.it8951 import IT8951
from IT8951_ePaper_Py.models import AreaImageInfo, DeviceInfo, DisplayArea, LoadImageInfo
from IT8951_ePaper_Py.spi_interface import SPIInterface, create_spi_interface


class EPaperDisplay:
    """High-level interface for IT8951 e-paper display.

    This class provides simplified methods for common e-paper operations,
    abstracting the low-level IT8951 protocol details.

    Attributes:
        width: Display width in pixels (after init).
        height: Display height in pixels (after init).
        size: Display size as (width, height) tuple (after init).
    """

    def __init__(
        self,
        vcom: float = DisplayConstants.DEFAULT_VCOM,
        spi_interface: SPIInterface | None = None,
        spi_speed_hz: int | None = None,
        a2_refresh_limit: int = 10,
        enhance_driving: bool = False,
    ) -> None:
        """Initialize e-paper display.

        Args:
            vcom: VCOM voltage setting (negative value).
            spi_interface: Optional SPI interface for testing. If provided,
                          spi_speed_hz is ignored.
            spi_speed_hz: Manual SPI speed override in Hz. If None, auto-detects
                         based on Pi version. Only used when spi_interface is None.
            a2_refresh_limit: Number of A2 refreshes before automatic INIT clear.
            enhance_driving: Enable enhanced driving for long cables or blurry displays.
                            Set to 0 to disable auto-clearing.
        """
        if spi_interface is None:
            spi_interface = create_spi_interface(spi_speed_hz=spi_speed_hz)
        self._controller = IT8951(spi_interface)
        self._vcom = vcom
        self._width = 0
        self._height = 0
        self._initialized = False
        self._a2_refresh_count = 0
        self._a2_refresh_limit = a2_refresh_limit
        self._enhance_driving = enhance_driving
        self._device_info: DeviceInfo | None = None

    def init(self) -> tuple[int, int]:
        """Initialize the display.

        Returns:
            Tuple of (width, height) in pixels.
        """
        if self._initialized:
            return (self._width, self._height)

        device_info = self._controller.init()
        self._device_info = device_info
        self._width = device_info.panel_width
        self._height = device_info.panel_height
        self._initialized = True

        self._controller.set_vcom(self._vcom)

        # Verify VCOM was set correctly
        actual_vcom = self._controller.get_vcom()
        if abs(actual_vcom - self._vcom) > 0.05:  # Allow 0.05V tolerance
            import warnings

            warnings.warn(
                f"VCOM mismatch detected! Requested: {self._vcom}V, Actual: {actual_vcom}V. "
                f"This may indicate a hardware issue or that the device rounded the value. "
                f"Consider using {actual_vcom}V in your configuration.",
                RuntimeWarning,
                stacklevel=2,
            )

        # Apply enhanced driving if requested
        if self._enhance_driving:
            self._controller.enhance_driving_capability()

        self.clear()

        return (self._width, self._height)

    def close(self) -> None:
        """Close the display and cleanup resources."""
        if self._controller:
            self._controller.close()
        self._initialized = False

    def clear(self, color: int = DisplayConstants.DEFAULT_CLEAR_COLOR) -> None:
        """Clear the display to a solid color.

        Args:
            color: Grayscale color value (0=black, DisplayConstants.GRAYSCALE_MAX=white).
        """
        self._ensure_initialized()

        buffer_size = self._width * self._height

        # Check for potential memory allocation issues
        max_buffer_size = DisplayConstants.MAX_WIDTH * DisplayConstants.MAX_HEIGHT
        if buffer_size > max_buffer_size:
            raise IT8951MemoryError(
                f"Buffer size ({buffer_size} bytes) exceeds maximum "
                f"({max_buffer_size} bytes) for display {self._width}x{self._height}"
            )

        try:
            # Create 8bpp data
            data_8bpp = bytes([color] * buffer_size)
        except MemoryError as e:
            raise IT8951MemoryError(f"Failed to allocate display buffer: {e}") from e

        # Pack to 4bpp format (default)
        packed_data = self._controller.pack_pixels(data_8bpp, PixelFormat.BPP_4)

        info = LoadImageInfo(
            source_buffer=packed_data,
            target_memory_addr=MemoryConstants.IMAGE_BUFFER_ADDR,
            pixel_format=PixelFormat.BPP_4,
        )

        self._controller.load_image_start(info)
        self._controller.load_image_write(packed_data)
        self._controller.load_image_end()

        area = DisplayArea(
            x=0,
            y=0,
            width=self._width,
            height=self._height,
            mode=DisplayMode.INIT,
        )

        self._controller.display_area(area, wait=True)

        # Reset A2 counter after clearing
        self._a2_refresh_count = 0

    def display_image(  # noqa: PLR0913
        self,
        image: Image.Image | str | Path | BinaryIO,
        x: int = 0,
        y: int = 0,
        mode: DisplayMode = DisplayMode.GC16,
        rotation: Rotation = Rotation.ROTATE_0,
        pixel_format: PixelFormat = PixelFormat.BPP_4,
    ) -> None:
        """Display an image on the e-paper.

        Args:
            image: PIL Image, file path, or file-like object.
            x: X coordinate for image placement.
            y: Y coordinate for image placement.
            mode: Display update mode.
            rotation: Image rotation.
            pixel_format: Pixel format (defaults to BPP_4, recommended by Waveshare).
                         Options: BPP_1, BPP_2, BPP_4, or BPP_8.
        """
        self._ensure_initialized()

        img = self._load_image(image)
        img = self._prepare_image(img, rotation)

        # Check image size limits
        if img.width > DisplayConstants.MAX_WIDTH or img.height > DisplayConstants.MAX_HEIGHT:
            raise IT8951MemoryError(
                f"Image dimensions ({img.width}x{img.height}) exceed maximum "
                f"({DisplayConstants.MAX_WIDTH}x{DisplayConstants.MAX_HEIGHT})"
            )

        if x + img.width > self._width:
            raise InvalidParameterError("Image exceeds display width")
        if y + img.height > self._height:
            raise InvalidParameterError("Image exceeds display height")

        # Validate and warn about alignment issues
        _, warnings = self.validate_alignment(x, y, img.width, img.height, pixel_format)
        if warnings:
            import warnings as warn_module

            for warning in warnings:
                warn_module.warn(warning, UserWarning, stacklevel=2)

        x = self._align_coordinate(x, pixel_format)
        y = self._align_coordinate(y, pixel_format)
        width = self._align_dimension(img.width, pixel_format)
        height = self._align_dimension(img.height, pixel_format)

        if width != img.width or height != img.height:
            img = img.resize((width, height), Image.Resampling.LANCZOS)

        # Get 8-bit pixel data
        data_8bpp = img.tobytes()

        # Pack pixels according to the requested format
        packed_data = self._controller.pack_pixels(data_8bpp, pixel_format)

        info = LoadImageInfo(
            source_buffer=packed_data,
            target_memory_addr=MemoryConstants.IMAGE_BUFFER_ADDR,
            pixel_format=pixel_format,
            rotate=rotation,
        )

        area_info = AreaImageInfo(
            area_x=x,
            area_y=y,
            area_w=width,
            area_h=height,
        )

        self._controller.load_image_area_start(info, area_info)
        self._controller.load_image_write(packed_data)
        self._controller.load_image_end()

        display_area = DisplayArea(
            x=x,
            y=y,
            width=width,
            height=height,
            mode=mode,
        )

        self._controller.display_area(display_area, wait=True)

        # Track A2 refreshes and auto-clear if needed
        if mode == DisplayMode.A2 and self._a2_refresh_limit > 0:
            self._a2_refresh_count += 1

            # Warn when approaching limit
            if self._a2_refresh_count == self._a2_refresh_limit - 1:
                import warnings

                warnings.warn(
                    f"A2 refresh count ({self._a2_refresh_count}) approaching limit "
                    f"({self._a2_refresh_limit}). Next A2 refresh will trigger auto-clear.",
                    UserWarning,
                    stacklevel=2,
                )

            # Auto-clear when limit reached
            elif self._a2_refresh_count >= self._a2_refresh_limit:
                self.clear()
                self._a2_refresh_count = 0

    def display_partial(
        self,
        image: Image.Image | NumpyArray,
        x: int,
        y: int,
        mode: DisplayMode = DisplayMode.DU,
    ) -> None:
        """Display a partial update.

        Args:
            image: Image to display (PIL or numpy array).
            x: X coordinate.
            y: Y coordinate.
            mode: Display mode (DU or A2 recommended for partial).
        """
        self._ensure_initialized()

        if isinstance(image, np.ndarray):
            if image.dtype != np.uint8:
                image = (image * DisplayConstants.GRAYSCALE_MAX).astype(np.uint8)
            image = Image.fromarray(image, mode="L")

        self.display_image(image, x, y, mode)

    def set_vcom(self, voltage: float) -> None:
        """Set VCOM voltage.

        Args:
            voltage: VCOM voltage (negative value).

        Raises:
            VCOMError: If voltage is out of range.

        Note:
            The method will verify the VCOM was set correctly and warn
            if there's a mismatch between requested and actual values.
        """
        self._ensure_initialized()
        self._controller.set_vcom(voltage)

        # Verify VCOM was set correctly
        actual_vcom = self._controller.get_vcom()
        if abs(actual_vcom - voltage) > 0.05:  # Allow 0.05V tolerance
            import warnings

            warnings.warn(
                f"VCOM mismatch after setting! Requested: {voltage}V, Actual: {actual_vcom}V. "
                f"The device may have rounded the value or there may be a hardware limitation.",
                RuntimeWarning,
                stacklevel=2,
            )
            self._vcom = actual_vcom  # Use actual value
        else:
            self._vcom = voltage

    def get_vcom(self) -> float:
        """Get current VCOM voltage.

        Returns:
            Current VCOM voltage.
        """
        self._ensure_initialized()
        return self._controller.get_vcom()

    def _create_vcom_test_pattern(self, width: int, height: int) -> Image.Image:
        """Create a test pattern for VCOM calibration.

        Args:
            width: Pattern width in pixels.
            height: Pattern height in pixels.

        Returns:
            Test pattern image with grayscale gradient.
        """
        from PIL import ImageDraw

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

    def find_optimal_vcom(
        self,
        start_voltage: float = -3.0,
        end_voltage: float = -1.0,
        step: float = 0.1,
        test_pattern: Image.Image | None = None,
    ) -> float:
        """Interactive VCOM calibration helper.

        This method helps find the optimal VCOM voltage for your display
        by allowing you to test different voltages and observe the results.

        Args:
            start_voltage: Starting VCOM voltage (default: -3.0V).
            end_voltage: Ending VCOM voltage (default: -1.0V).
            step: Voltage step size (default: 0.1V).
            test_pattern: Optional custom test pattern image.
                         If None, uses a grayscale gradient pattern.

        Returns:
            The selected optimal VCOM voltage.

        Raises:
            VCOMError: If voltage range is invalid.

        Example:
            >>> display = EPaperDisplay()
            >>> display.init()
            >>> optimal_vcom = display.find_optimal_vcom()
            >>> print(f"Optimal VCOM: {optimal_vcom}V")
        """
        import time

        self._ensure_initialized()

        # Validate voltage range
        if start_voltage > end_voltage:
            start_voltage, end_voltage = end_voltage, start_voltage

        if start_voltage < DisplayConstants.MIN_VCOM or end_voltage > DisplayConstants.MAX_VCOM:
            raise VCOMError(
                f"Voltage range must be between {DisplayConstants.MIN_VCOM}V "
                f"and {DisplayConstants.MAX_VCOM}V"
            )

        # Create default test pattern if not provided
        if test_pattern is None:
            pattern_width = min(800, self._width)
            pattern_height = min(600, self._height)
            test_pattern = self._create_vcom_test_pattern(pattern_width, pattern_height)

        print("\nVCOM Calibration Helper")
        print("======================")
        print(f"Testing VCOM range: {start_voltage}V to {end_voltage}V (step: {step}V)")
        print("\nInstructions:")
        print("1. Observe the display quality at each voltage")
        print("2. Look for optimal contrast without artifacts")
        print("3. Press Enter to try next voltage")
        print("4. Type 'select' when you find the best voltage")
        print("5. Type 'back' to go to previous voltage")
        print("6. Type 'quit' to cancel\n")

        current_voltage = start_voltage
        previous_voltage = None

        while True:
            # Set and display current VCOM
            print(f"\nTesting VCOM: {current_voltage:.2f}V")
            self.set_vcom(current_voltage)
            time.sleep(0.1)  # Allow voltage to settle

            # Clear and display test pattern
            self.clear()
            x = (self._width - test_pattern.width) // 2
            y = (self._height - test_pattern.height) // 2
            self.display_image(test_pattern, x=x, y=y, mode=DisplayMode.GC16)

            # Get user input
            user_input = input("Action (Enter/select/back/quit): ").strip().lower()

            if user_input == "select":
                print(f"\nSelected optimal VCOM: {current_voltage:.2f}V")
                print(f"Add to your code: EPaperDisplay(vcom={current_voltage:.2f})")
                return current_voltage

            if user_input == "back" and previous_voltage is not None:
                current_voltage, previous_voltage = previous_voltage, current_voltage

            elif user_input == "quit":
                print("\nCalibration cancelled")
                return self._vcom

            else:  # Enter or empty - go to next voltage
                previous_voltage = current_voltage
                current_voltage += step

                if current_voltage > end_voltage:
                    print("\nReached end of range. Please select a voltage or quit.")
                    current_voltage = previous_voltage

    def sleep(self) -> None:
        """Put display into sleep mode."""
        self._ensure_initialized()
        self._controller.sleep()

    def standby(self) -> None:
        """Put display into standby mode."""
        self._ensure_initialized()
        self._controller.standby()

    def _load_image(self, image: Image.Image | str | Path | BinaryIO) -> Image.Image:
        """Load image from various sources.

        Args:
            image: Image source.

        Returns:
            PIL Image in grayscale mode.
        """
        if isinstance(image, Image.Image):
            img = image
        elif isinstance(image, str | Path) or hasattr(image, "read"):
            img = Image.open(image)
        else:
            raise InvalidParameterError("Invalid image source")

        if img.mode != "L":
            img = img.convert("L")

        return img

    def _prepare_image(self, image: Image.Image, rotation: Rotation) -> Image.Image:
        """Prepare image for display.

        Args:
            image: Input image.
            rotation: Rotation to apply.

        Returns:
            Prepared image.
        """
        if rotation == Rotation.ROTATE_90:
            image = image.rotate(RotationAngle.ANGLE_90, expand=True)
        elif rotation == Rotation.ROTATE_180:
            image = image.rotate(RotationAngle.ANGLE_180)
        elif rotation == Rotation.ROTATE_270:
            image = image.rotate(RotationAngle.ANGLE_270, expand=True)

        return image

    def _align_coordinate(self, coord: int, pixel_format: PixelFormat | None = None) -> int:
        """Align coordinate to appropriate boundary based on pixel format.

        Args:
            coord: Input coordinate.
            pixel_format: Pixel format (defaults to current format).

        Returns:
            Aligned coordinate.
        """
        if pixel_format is None:
            pixel_format = PixelFormat.BPP_4  # Default format

        # 1bpp requires 32-bit (32 pixel) alignment per wiki documentation
        if pixel_format == PixelFormat.BPP_1:
            alignment = DisplayConstants.PIXEL_ALIGNMENT_1BPP
        else:
            alignment = DisplayConstants.PIXEL_ALIGNMENT

        return (coord // alignment) * alignment

    def _align_dimension(self, dim: int, pixel_format: PixelFormat | None = None) -> int:
        """Align dimension to appropriate multiple based on pixel format.

        Args:
            dim: Input dimension.
            pixel_format: Pixel format (defaults to current format).

        Returns:
            Aligned dimension.
        """
        if pixel_format is None:
            pixel_format = PixelFormat.BPP_4  # Default format

        # 1bpp requires 32-bit (32 pixel) alignment per wiki documentation
        if pixel_format == PixelFormat.BPP_1:
            alignment = DisplayConstants.PIXEL_ALIGNMENT_1BPP
        else:
            alignment = DisplayConstants.PIXEL_ALIGNMENT

        return ((dim + alignment - 1) // alignment) * alignment

    def _ensure_initialized(self) -> None:
        """Ensure display is initialized."""
        if not self._initialized:
            raise DisplayError("Display not initialized. Call init() first.")

    def _requires_special_1bpp_alignment(self) -> bool:
        """Check if the current model requires special 32-bit alignment for 1bpp.

        Returns:
            True if the model requires special alignment for 1bpp mode.
        """
        if not self._device_info:
            return True  # Conservative default

        # According to wiki, certain models require 32-bit alignment for 1bpp
        # This is typically indicated by specific LUT versions
        # For now, we'll be conservative and always use 32-bit alignment for 1bpp
        return True

    def validate_alignment(
        self, x: int, y: int, width: int, height: int, pixel_format: PixelFormat | None = None
    ) -> tuple[bool, list[str]]:
        """Validate alignment requirements for display operation.

        Args:
            x: X coordinate.
            y: Y coordinate.
            width: Image width.
            height: Image height.
            pixel_format: Pixel format (defaults to BPP_4).

        Returns:
            Tuple of (is_valid, warnings) where warnings contains any alignment issues.
        """
        warnings: list[str] = []

        if pixel_format is None:
            pixel_format = PixelFormat.BPP_4

        # Determine required alignment
        if pixel_format == PixelFormat.BPP_1:
            alignment = DisplayConstants.PIXEL_ALIGNMENT_1BPP
            alignment_desc = "32-pixel (4-byte)"
        else:
            alignment = DisplayConstants.PIXEL_ALIGNMENT
            alignment_desc = "4-pixel"

        # Check coordinate alignment
        if x % alignment != 0:
            warnings.append(
                f"X coordinate {x} not aligned to {alignment_desc} boundary. "
                f"Will be adjusted to {self._align_coordinate(x, pixel_format)}"
            )

        if y % alignment != 0:
            warnings.append(
                f"Y coordinate {y} not aligned to {alignment_desc} boundary. "
                f"Will be adjusted to {self._align_coordinate(y, pixel_format)}"
            )

        # Check dimension alignment
        if width % alignment != 0:
            warnings.append(
                f"Width {width} not aligned to {alignment_desc} boundary. "
                f"Will be adjusted to {self._align_dimension(width, pixel_format)}"
            )

        if height % alignment != 0:
            warnings.append(
                f"Height {height} not aligned to {alignment_desc} boundary. "
                f"Will be adjusted to {self._align_dimension(height, pixel_format)}"
            )

        # Special warning for 1bpp
        if pixel_format == PixelFormat.BPP_1 and warnings:
            warnings.insert(
                0,
                "Note: 1bpp mode requires strict 32-pixel alignment on some models. "
                "Image may be cropped or padded to meet requirements.",
            )

        return (len(warnings) == 0, warnings)

    @property
    def width(self) -> int:
        """Get display width in pixels.

        Returns:
            int: Display width in pixels.

        Raises:
            DisplayError: If display not initialized.
        """
        self._ensure_initialized()
        return self._width

    @property
    def height(self) -> int:
        """Get display height in pixels.

        Returns:
            int: Display height in pixels.

        Raises:
            DisplayError: If display not initialized.
        """
        self._ensure_initialized()
        return self._height

    @property
    def size(self) -> tuple[int, int]:
        """Get display size as (width, height).

        Returns:
            tuple[int, int]: Display dimensions as (width, height).

        Raises:
            DisplayError: If display not initialized.
        """
        self._ensure_initialized()
        return (self._width, self._height)

    @property
    def a2_refresh_count(self) -> int:
        """Get current A2 refresh count.

        Returns:
            int: Number of A2 refreshes since last clear.
        """
        return self._a2_refresh_count

    @property
    def a2_refresh_limit(self) -> int:
        """Get A2 refresh limit before auto-clear.

        Returns:
            int: Number of A2 refreshes before auto-clear (0 = disabled).
        """
        return self._a2_refresh_limit

    def is_enhanced_driving_enabled(self) -> bool:
        """Check if enhanced driving capability is enabled.

        Returns:
            bool: True if enhanced driving is enabled, False otherwise.
        """
        return self._controller.is_enhanced_driving_enabled()

    def dump_registers(self) -> dict[str, int]:
        """Dump common register values for debugging.

        Returns:
            dict[str, int]: Dictionary of register names to values.
        """
        return self._controller.dump_registers()
