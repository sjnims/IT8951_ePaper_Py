"""High-level display interface for IT8951 e-paper."""

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
from IT8951_ePaper_Py.exceptions import DisplayError, InvalidParameterError
from IT8951_ePaper_Py.it8951 import IT8951
from IT8951_ePaper_Py.models import AreaImageInfo, DisplayArea, LoadImageInfo
from IT8951_ePaper_Py.spi_interface import SPIInterface


class EPaperDisplay:
    """High-level interface for IT8951 e-paper display."""

    def __init__(
        self,
        vcom: float = DisplayConstants.DEFAULT_VCOM,
        spi_interface: SPIInterface | None = None,
    ) -> None:
        """Initialize e-paper display.

        Args:
            vcom: VCOM voltage setting (negative value).
            spi_interface: Optional SPI interface for testing.
        """
        self._controller = IT8951(spi_interface)
        self._vcom = vcom
        self._width = 0
        self._height = 0
        self._initialized = False

    def init(self) -> tuple[int, int]:
        """Initialize the display.

        Returns:
            Tuple of (width, height) in pixels.
        """
        if self._initialized:
            return (self._width, self._height)

        device_info = self._controller.init()
        self._width = device_info.panel_width
        self._height = device_info.panel_height
        self._initialized = True

        self._controller.set_vcom(self._vcom)
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
            color: Grayscale color value (0=black, 255=white).
        """
        self._ensure_initialized()

        buffer_size = self._width * self._height
        data = bytes([color] * buffer_size)

        info = LoadImageInfo(
            source_buffer=data,
            target_memory_addr=MemoryConstants.IMAGE_BUFFER_ADDR,
            pixel_format=PixelFormat.BPP_8,
        )

        self._controller.load_image_start(info)
        self._controller.load_image_write(data)
        self._controller.load_image_end()

        area = DisplayArea(
            x=0,
            y=0,
            width=self._width,
            height=self._height,
            mode=DisplayMode.INIT,
        )

        self._controller.display_area(area, wait=True)

    def display_image(
        self,
        image: Image.Image | str | Path | BinaryIO,
        x: int = 0,
        y: int = 0,
        mode: DisplayMode = DisplayMode.GC16,
        rotation: Rotation = Rotation.ROTATE_0,
    ) -> None:
        """Display an image on the e-paper.

        Args:
            image: PIL Image, file path, or file-like object.
            x: X coordinate for image placement.
            y: Y coordinate for image placement.
            mode: Display update mode.
            rotation: Image rotation.
        """
        self._ensure_initialized()

        img = self._load_image(image)
        img = self._prepare_image(img, rotation)

        if x + img.width > self._width:
            raise InvalidParameterError("Image exceeds display width")
        if y + img.height > self._height:
            raise InvalidParameterError("Image exceeds display height")

        x = self._align_coordinate(x)
        y = self._align_coordinate(y)
        width = self._align_dimension(img.width)
        height = self._align_dimension(img.height)

        if width != img.width or height != img.height:
            img = img.resize((width, height), Image.Resampling.LANCZOS)

        data = img.tobytes()

        info = LoadImageInfo(
            source_buffer=data,
            target_memory_addr=MemoryConstants.IMAGE_BUFFER_ADDR,
            pixel_format=PixelFormat.BPP_8,
            rotate=rotation,
        )

        area_info = AreaImageInfo(
            area_x=x,
            area_y=y,
            area_w=width,
            area_h=height,
        )

        self._controller.load_image_area_start(info, area_info)
        self._controller.load_image_write(data)
        self._controller.load_image_end()

        display_area = DisplayArea(
            x=x,
            y=y,
            width=width,
            height=height,
            mode=mode,
        )

        self._controller.display_area(display_area, wait=True)

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
                image = (image * 255).astype(np.uint8)
            image = Image.fromarray(image, mode="L")

        self.display_image(image, x, y, mode)

    def set_vcom(self, voltage: float) -> None:
        """Set VCOM voltage.

        Args:
            voltage: VCOM voltage (negative value).
        """
        self._ensure_initialized()
        self._controller.set_vcom(voltage)
        self._vcom = voltage

    def get_vcom(self) -> float:
        """Get current VCOM voltage.

        Returns:
            Current VCOM voltage.
        """
        self._ensure_initialized()
        return self._controller.get_vcom()

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

    def _align_coordinate(self, coord: int) -> int:
        """Align coordinate to 4-pixel boundary.

        Args:
            coord: Input coordinate.

        Returns:
            Aligned coordinate.
        """
        return (coord // 4) * 4

    def _align_dimension(self, dim: int) -> int:
        """Align dimension to 4-pixel multiple.

        Args:
            dim: Input dimension.

        Returns:
            Aligned dimension.
        """
        return ((dim + 3) // 4) * 4

    def _ensure_initialized(self) -> None:
        """Ensure display is initialized."""
        if not self._initialized:
            raise DisplayError("Display not initialized. Call init() first.")

    @property
    def width(self) -> int:
        """Get display width in pixels."""
        self._ensure_initialized()
        return self._width

    @property
    def height(self) -> int:
        """Get display height in pixels."""
        self._ensure_initialized()
        return self._height

    @property
    def size(self) -> tuple[int, int]:
        """Get display size as (width, height)."""
        self._ensure_initialized()
        return (self._width, self._height)
