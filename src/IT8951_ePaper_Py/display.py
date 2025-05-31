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

from enum import Enum
from pathlib import Path
from types import TracebackType
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
    PowerState,
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
from IT8951_ePaper_Py.utils import timed_operation


class VCOMCalibrationState(Enum):
    """States for VCOM calibration state machine."""

    TESTING = "testing"
    SELECTED = "selected"
    CANCELLED = "cancelled"
    BACK = "back"


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
        vcom: float,
        spi_interface: SPIInterface | None = None,
        spi_speed_hz: int | None = None,
        a2_refresh_limit: int = 10,
        enhance_driving: bool = False,
    ) -> None:
        """Initialize e-paper display.

        Args:
            vcom: VCOM voltage setting (negative value). This MUST match your
                  display's calibrated VCOM value for optimal image quality.
            spi_interface: Optional SPI interface for testing. If provided,
                          spi_speed_hz is ignored.
            spi_speed_hz: Manual SPI speed override in Hz. If None, auto-detects
                         based on Pi version. Only used when spi_interface is None.
            a2_refresh_limit: Number of A2 refreshes before automatic INIT clear.
                             Set to 0 to disable auto-clearing.
            enhance_driving: Enable enhanced driving for long cables or blurry displays.
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

        # Initialize auto-sleep timer
        import time

        self._last_activity_time = time.time()
        self._auto_sleep_timeout: float | None = None

    @timed_operation("init")
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
                stacklevel=3,
            )

        # Apply enhanced driving if requested
        if self._enhance_driving:
            self._controller.enhance_driving_capability()

        self.clear()

        return (self._width, self._height)

    @property
    def power_state(self) -> PowerState:
        """Get the current power state of the display.

        Returns:
            PowerState: The current power state (ACTIVE, STANDBY, or SLEEP).
        """
        return self._controller.power_state

    def close(self) -> None:
        """Close the display and cleanup resources."""
        if self._controller:
            self._controller.close()
        self._initialized = False

    @timed_operation("clear")
    def clear(self, color: int = DisplayConstants.DEFAULT_CLEAR_COLOR) -> None:
        """Clear the display to a solid color.

        Args:
            color: Grayscale color value (0=black, DisplayConstants.GRAYSCALE_MAX=white).
        """
        self._ensure_initialized()
        self.check_auto_sleep()
        self._update_activity_time()

        buffer_size = self._width * self._height

        # Check for potential memory allocation issues
        max_buffer_size = DisplayConstants.MAX_WIDTH * DisplayConstants.MAX_HEIGHT
        if buffer_size > max_buffer_size:
            raise IT8951MemoryError(
                f"Buffer size ({buffer_size} bytes) exceeds maximum "
                f"({max_buffer_size} bytes) for display {self._width}x{self._height}"
            )

        try:
            # Create 8bpp data more efficiently using bytes multiplication
            data_8bpp = bytes([color]) * buffer_size
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

    def _validate_image_params(
        self,
        img: Image.Image,
        x: int,
        y: int,
        pixel_format: PixelFormat,
    ) -> tuple[int, int, int, int, Image.Image]:
        """Validate image parameters and return aligned values.

        Args:
            img: PIL Image to validate.
            x: X coordinate.
            y: Y coordinate.
            pixel_format: Pixel format for alignment.

        Returns:
            Tuple of (aligned_x, aligned_y, aligned_width, aligned_height, adjusted_image).

        Raises:
            IT8951MemoryError: If image dimensions exceed maximum.
            InvalidParameterError: If image exceeds display bounds.
        """
        # Check image size limits
        if img.width > DisplayConstants.MAX_WIDTH or img.height > DisplayConstants.MAX_HEIGHT:
            raise IT8951MemoryError(
                f"Image dimensions ({img.width}x{img.height}) exceed maximum "
                f"({DisplayConstants.MAX_WIDTH}x{DisplayConstants.MAX_HEIGHT})"
            )

        # Estimate and check memory usage
        memory_usage = self._estimate_memory_usage(img.width, img.height, pixel_format)

        if memory_usage > MemoryConstants.SAFE_IMAGE_MEMORY_BYTES:
            raise IT8951MemoryError(
                f"Image memory usage ({memory_usage:,} bytes) exceeds safe limit "
                f"({MemoryConstants.SAFE_IMAGE_MEMORY_BYTES:,} bytes). "
                f"Consider using a lower resolution or different pixel format."
            )

        if memory_usage > MemoryConstants.WARNING_THRESHOLD_BYTES:
            import warnings

            warnings.warn(
                f"Large image memory usage: {memory_usage:,} bytes "
                f"({memory_usage / (1024 * 1024):.1f} MB). "
                f"Consider using a more efficient pixel format (4bpp, 2bpp, or 1bpp) "
                f"to improve performance and reduce memory usage.",
                UserWarning,
                stacklevel=5,
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
                warn_module.warn(warning, UserWarning, stacklevel=4)

        # Apply alignment
        aligned_x = self._align_coordinate(x, pixel_format)
        aligned_y = self._align_coordinate(y, pixel_format)
        aligned_width = self._align_dimension(img.width, pixel_format)
        aligned_height = self._align_dimension(img.height, pixel_format)

        # Resize image if needed for alignment
        if aligned_width != img.width or aligned_height != img.height:
            img = img.resize((aligned_width, aligned_height), Image.Resampling.LANCZOS)

        return aligned_x, aligned_y, aligned_width, aligned_height, img

    def _estimate_memory_usage(self, width: int, height: int, pixel_format: PixelFormat) -> int:
        """Estimate memory usage for an image operation.

        Args:
            width: Image width in pixels.
            height: Image height in pixels.
            pixel_format: Pixel format for the operation.

        Returns:
            Estimated memory usage in bytes.
        """
        pixels = width * height

        # Calculate bytes based on pixel format
        if pixel_format == PixelFormat.BPP_8:
            return pixels  # 1 byte per pixel
        if pixel_format == PixelFormat.BPP_4:
            return (pixels + 1) // 2  # 2 pixels per byte
        if pixel_format == PixelFormat.BPP_2:
            return (pixels + 3) // 4  # 4 pixels per byte
        if pixel_format == PixelFormat.BPP_1:
            return (pixels + 7) // 8  # 8 pixels per byte
        return pixels  # Default to worst case

    def _track_a2_refresh(self, mode: DisplayMode) -> None:
        """Track A2 mode refreshes and handle auto-clearing.

        Args:
            mode: Display mode being used.
        """
        if mode != DisplayMode.A2 or self._a2_refresh_limit <= 0:
            return

        self._a2_refresh_count += 1

        # Warn when approaching limit
        if self._a2_refresh_count == self._a2_refresh_limit - 1:
            import warnings

            warnings.warn(
                f"A2 refresh count ({self._a2_refresh_count}) approaching limit "
                f"({self._a2_refresh_limit}). Next A2 refresh will trigger auto-clear.",
                UserWarning,
                stacklevel=4,
            )

        # Auto-clear when limit reached
        elif self._a2_refresh_count >= self._a2_refresh_limit:
            self.clear()
            self._a2_refresh_count = 0

    @timed_operation("display_image")
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
        self.check_auto_sleep()
        self._update_activity_time()

        # Load and prepare image
        img = self._load_image(image)
        img = self._prepare_image(img, rotation)

        # Validate and align parameters
        x, y, width, height, img = self._validate_image_params(img, x, y, pixel_format)

        # Get 8-bit pixel data and pack according to format
        data_8bpp = img.tobytes()
        packed_data = self._controller.pack_pixels(data_8bpp, pixel_format)

        # Load image to controller memory
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

        # Display the image
        display_area = DisplayArea(
            x=x,
            y=y,
            width=width,
            height=height,
            mode=mode,
        )

        self._controller.display_area(display_area, wait=True)

        # Track A2 refreshes
        self._track_a2_refresh(mode)

    @timed_operation("display_image_progressive")
    def display_image_progressive(  # noqa: PLR0913
        self,
        image: Image.Image | str | Path | BinaryIO,
        x: int = 0,
        y: int = 0,
        mode: DisplayMode = DisplayMode.GC16,
        rotation: Rotation = Rotation.ROTATE_0,
        pixel_format: PixelFormat = PixelFormat.BPP_4,
        chunk_height: int = 256,
    ) -> None:
        """Display a large image progressively in chunks to manage memory usage.

        This method is useful for very large images that might exceed memory
        limits if loaded all at once. It processes the image in horizontal strips.

        Args:
            image: PIL Image, file path, or file-like object.
            x: X coordinate for image placement.
            y: Y coordinate for image placement.
            mode: Display update mode.
            rotation: Image rotation.
            pixel_format: Pixel format (defaults to BPP_4).
            chunk_height: Height of each chunk in pixels. Smaller values use
                         less memory but require more operations.

        Note:
            Chunk boundaries are automatically aligned based on pixel format
            requirements. The actual chunk height may be adjusted to meet
            alignment constraints.
        """
        self._ensure_initialized()
        self.check_auto_sleep()
        self._update_activity_time()

        # Load and prepare image
        img = self._load_image(image)
        img = self._prepare_image(img, rotation)

        # Validate overall image placement
        if x + img.width > self._width:
            raise InvalidParameterError("Image exceeds display width")
        if y + img.height > self._height:
            raise InvalidParameterError("Image exceeds display height")

        # Align chunk height to pixel format requirements
        if pixel_format == PixelFormat.BPP_1:
            # 1bpp requires 32-pixel alignment
            chunk_height = (chunk_height // 32) * 32
            if chunk_height == 0:
                chunk_height = 32
        else:
            # Other formats use 4-pixel alignment
            chunk_height = (chunk_height // 4) * 4
            if chunk_height == 0:
                chunk_height = 4

        # Process image in chunks
        remaining_height = img.height
        current_y = 0

        while remaining_height > 0:
            # Calculate chunk dimensions
            this_chunk_height = min(chunk_height, remaining_height)

            # Align chunk dimensions
            aligned_chunk_height = self._align_dimension(this_chunk_height, pixel_format)

            # Extract chunk from image
            chunk_box = (0, current_y, img.width, current_y + this_chunk_height)
            chunk = img.crop(chunk_box)

            # Resize chunk if alignment required it
            if aligned_chunk_height != this_chunk_height:
                chunk = chunk.resize((img.width, aligned_chunk_height), Image.Resampling.LANCZOS)

            # Display this chunk
            chunk_x = x
            chunk_y = y + current_y

            # Validate and align chunk parameters
            aligned_x = self._align_coordinate(chunk_x, pixel_format)
            aligned_y = self._align_coordinate(chunk_y, pixel_format)
            aligned_width = self._align_dimension(chunk.width, pixel_format)

            # Get pixel data and pack
            data_8bpp = chunk.tobytes()
            packed_data = self._controller.pack_pixels(data_8bpp, pixel_format)

            # Load chunk to controller memory
            info = LoadImageInfo(
                source_buffer=packed_data,
                target_memory_addr=MemoryConstants.IMAGE_BUFFER_ADDR,
                pixel_format=pixel_format,
                rotate=Rotation.ROTATE_0,  # Rotation already applied to full image
            )

            area_info = AreaImageInfo(
                area_x=aligned_x,
                area_y=aligned_y,
                area_w=aligned_width,
                area_h=aligned_chunk_height,
            )

            self._controller.load_image_area_start(info, area_info)
            self._controller.load_image_write(packed_data)
            self._controller.load_image_end()

            # Display this chunk
            display_area = DisplayArea(
                x=aligned_x,
                y=aligned_y,
                width=aligned_width,
                height=aligned_chunk_height,
                mode=mode,
            )

            self._controller.display_area(display_area, wait=True)

            # Move to next chunk
            current_y += this_chunk_height
            remaining_height -= this_chunk_height

        # Track A2 refreshes (only once for the entire progressive operation)
        self._track_a2_refresh(mode)

    @timed_operation("display_partial")
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

    def _vcom_calibration_state_machine(  # noqa: PLR0913
        self,
        action: str,
        current_voltage: float,
        previous_voltage: float | None,
        start_voltage: float,
        end_voltage: float,
        step: float,
    ) -> tuple[VCOMCalibrationState, float, float | None]:
        """State machine for VCOM calibration.

        Args:
            action: User action input.
            current_voltage: Current VCOM voltage.
            previous_voltage: Previous VCOM voltage.
            start_voltage: Start of voltage range.
            end_voltage: End of voltage range.
            step: Voltage step size.

        Returns:
            Tuple of (state, new_current_voltage, new_previous_voltage).
        """
        if action == "select":
            return VCOMCalibrationState.SELECTED, current_voltage, previous_voltage

        if action == "quit":
            return VCOMCalibrationState.CANCELLED, current_voltage, previous_voltage

        if action == "back" and previous_voltage is not None:
            return VCOMCalibrationState.TESTING, previous_voltage, current_voltage

        # Default: go to next voltage
        new_previous = current_voltage
        new_current = current_voltage + step

        if new_current > end_voltage:
            print("\nReached end of range. Please select a voltage or quit.")
            return VCOMCalibrationState.TESTING, current_voltage, previous_voltage

        return VCOMCalibrationState.TESTING, new_current, new_previous

    def _display_vcom_test_pattern(self, voltage: float, test_pattern: Image.Image) -> None:
        """Display test pattern at given VCOM voltage.

        Args:
            voltage: VCOM voltage to test.
            test_pattern: Test pattern image.
        """
        import time

        print(f"\nTesting VCOM: {voltage:.2f}V")
        self.set_vcom(voltage)
        time.sleep(0.1)  # Allow voltage to settle

        # Clear and display test pattern
        self.clear()
        x = (self._width - test_pattern.width) // 2
        y = (self._height - test_pattern.height) // 2
        self.display_image(test_pattern, x=x, y=y, mode=DisplayMode.GC16)

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
        state = VCOMCalibrationState.TESTING

        while state == VCOMCalibrationState.TESTING:
            # Display test pattern at current voltage
            self._display_vcom_test_pattern(current_voltage, test_pattern)

            # Get user input
            user_input = input("Action (Enter/select/back/quit): ").strip().lower()

            # Process input through state machine
            state, current_voltage, previous_voltage = self._vcom_calibration_state_machine(
                user_input, current_voltage, previous_voltage, start_voltage, end_voltage, step
            )

        # Handle final state
        if state == VCOMCalibrationState.SELECTED:
            print(f"\nSelected optimal VCOM: {current_voltage:.2f}V")
            print(f"Add to your code: EPaperDisplay(vcom={current_voltage:.2f})")
            return current_voltage
        # CANCELLED
        print("\nCalibration cancelled")
        return self._vcom

    def sleep(self) -> None:
        """Put display into sleep mode."""
        self._ensure_initialized()
        self._controller.sleep()

    def standby(self) -> None:
        """Put display into standby mode."""
        self._ensure_initialized()
        self._controller.standby()

    def wake(self) -> None:
        """Wake display from sleep or standby mode."""
        self._ensure_initialized()
        self._controller.wake()
        self._update_activity_time()

    def set_auto_sleep_timeout(self, timeout_seconds: float | None) -> None:
        """Set auto-sleep timeout.

        The display will automatically enter sleep mode after the specified
        period of inactivity. Set to None to disable auto-sleep.

        Args:
            timeout_seconds: Timeout in seconds, or None to disable auto-sleep.
                            Must be positive if provided.

        Raises:
            InvalidParameterError: If timeout is not positive.
        """
        if timeout_seconds is not None and timeout_seconds <= 0:
            raise InvalidParameterError("Auto-sleep timeout must be positive")

        self._auto_sleep_timeout = timeout_seconds
        self._update_activity_time()

    def _update_activity_time(self) -> None:
        """Update the last activity timestamp."""
        import time

        self._last_activity_time = time.time()

    def check_auto_sleep(self) -> None:
        """Check if auto-sleep timeout has been reached and sleep if necessary.

        This method is automatically called during display operations when auto-sleep
        is enabled. You can also call it manually to check for timeout conditions,
        which is useful for applications with long periods between display updates.

        Note:
            Does nothing if auto-sleep timeout is not set (None).
        """
        if self._auto_sleep_timeout is None:
            return

        import time

        current_time = time.time()
        inactive_time = current_time - self._last_activity_time

        if inactive_time >= self._auto_sleep_timeout and self.power_state == PowerState.ACTIVE:
            self.sleep()

    def __enter__(self) -> "EPaperDisplay":
        """Context manager entry - initialize display."""
        self.init()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit - close display and optionally sleep."""
        if self._auto_sleep_timeout is not None and self.power_state == PowerState.ACTIVE:
            self.sleep()
        self.close()

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

        # Check all parameters using a structured approach
        params = [
            ("X coordinate", x, self._align_coordinate),
            ("Y coordinate", y, self._align_coordinate),
            ("Width", width, self._align_dimension),
            ("Height", height, self._align_dimension),
        ]

        for param_name, value, align_func in params:
            if value % alignment != 0:
                aligned_value = align_func(value, pixel_format)
                warnings.append(
                    f"{param_name} {value} not aligned to {alignment_desc} boundary. "
                    f"Will be adjusted to {aligned_value}"
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

    def get_device_status(self) -> dict[str, str | int | float | bool | None]:
        """Get comprehensive device status information.

        Returns device information including hardware specs, power state,
        VCOM voltage, and other runtime status.

        Returns:
            dict: Device status with the following keys:
                - panel_width: Display width in pixels
                - panel_height: Display height in pixels
                - memory_address: Image buffer memory address
                - fw_version: Firmware version
                - lut_version: LUT version
                - power_state: Current power state (ACTIVE, STANDBY, or SLEEP)
                - vcom_voltage: Current VCOM voltage
                - a2_refresh_count: Current A2 refresh counter
                - a2_refresh_limit: A2 refresh limit setting
                - auto_sleep_timeout: Auto-sleep timeout in seconds (or None)
                - enhanced_driving: Whether enhanced driving is enabled

        Raises:
            DisplayError: If display not initialized.
        """
        self._ensure_initialized()

        status: dict[str, str | int | float | bool | None] = {}

        # Add device info
        if self._device_info:
            status["panel_width"] = self._device_info.panel_width
            status["panel_height"] = self._device_info.panel_height
            status["memory_address"] = hex(self._device_info.memory_address)
            # Ensure versions are strings
            fw_ver = self._device_info.fw_version
            status["fw_version"] = fw_ver if isinstance(fw_ver, str) else str(fw_ver)
            lut_ver = self._device_info.lut_version
            status["lut_version"] = lut_ver if isinstance(lut_ver, str) else str(lut_ver)

        # Add runtime status
        status["power_state"] = self.power_state.name
        status["vcom_voltage"] = self._vcom
        status["a2_refresh_count"] = self._a2_refresh_count
        status["a2_refresh_limit"] = self._a2_refresh_limit
        status["auto_sleep_timeout"] = self._auto_sleep_timeout
        status["enhanced_driving"] = self.is_enhanced_driving_enabled()

        return status
