"""Tests for high-level display interface."""

import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from pytest_mock import MockerFixture

from IT8951_ePaper_Py.constants import DisplayMode, MemoryConstants, Rotation
from IT8951_ePaper_Py.display import EPaperDisplay
from IT8951_ePaper_Py.exceptions import DisplayError, InvalidParameterError, IT8951MemoryError
from IT8951_ePaper_Py.spi_interface import MockSPI


class TestEPaperDisplay:
    """Test EPaperDisplay class."""

    @pytest.fixture
    def mock_spi(self) -> MockSPI:
        """Create mock SPI interface."""
        return MockSPI()

    @pytest.fixture
    def display(self, mock_spi: MockSPI) -> EPaperDisplay:
        """Create EPaperDisplay with mock SPI."""
        return EPaperDisplay(spi_interface=mock_spi)

    @pytest.fixture
    def initialized_display(
        self, display: EPaperDisplay, mock_spi: MockSPI, mocker: MockerFixture
    ) -> EPaperDisplay:
        """Create and initialize EPaperDisplay."""
        # Data for _get_device_info (20 values)
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        # Data for _enable_packed_write register read
        mock_spi.set_read_data([0x0000])

        # Mock clear to avoid complex setup
        mocker.patch.object(display, "clear")

        display.init()
        return display

    @pytest.fixture
    def enhanced_display(self, mock_spi: MockSPI, mocker: MockerFixture) -> EPaperDisplay:
        """Create EPaperDisplay with enhanced driving enabled."""
        display = EPaperDisplay(spi_interface=mock_spi, enhance_driving=True)

        # Data for _get_device_info (20 values)
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        # Data for _enable_packed_write register read
        mock_spi.set_read_data([0x0000])

        # Mock clear to avoid complex setup
        mocker.patch.object(display, "clear")

        display.init()
        return display

    def test_init(self, display: EPaperDisplay, mock_spi: MockSPI, mocker: MockerFixture) -> None:
        """Test display initialization."""
        # Data for _get_device_info (20 values)
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        # Data for _enable_packed_write register read
        mock_spi.set_read_data([0x0000])

        # Mock clear to avoid complex setup
        mocker.patch.object(display, "clear")

        width, height = display.init()

        assert width == 1024
        assert height == 768
        assert display._initialized  # type: ignore[reportPrivateUsage]

        width2, height2 = display.init()
        assert (width2, height2) == (width, height)

    def test_close(self, initialized_display: EPaperDisplay) -> None:
        """Test display close."""
        initialized_display.close()
        assert not initialized_display._initialized  # type: ignore[reportPrivateUsage]

    def test_clear(self, initialized_display: EPaperDisplay, mock_spi: MockSPI) -> None:
        """Test display clear."""
        mock_spi.set_read_data([0])
        initialized_display.clear()

        buffer = mock_spi.get_data_buffer()

        assert any(len(chunk) > 0 for chunk in [buffer])

        initialized_display.clear(color=0x00)

    def test_display_image_from_pil(
        self, initialized_display: EPaperDisplay, mock_spi: MockSPI
    ) -> None:
        """Test displaying PIL image."""
        img = Image.new("L", (800, 600), color=128)
        mock_spi.set_read_data([0])

        initialized_display.display_image(img, x=0, y=0, mode=DisplayMode.GC16)

        buffer = mock_spi.get_data_buffer()
        assert len(buffer) > 0

    def test_display_image_from_file(
        self, initialized_display: EPaperDisplay, mock_spi: MockSPI, tmp_path: Path
    ) -> None:
        """Test displaying image from file."""
        img = Image.new("L", (100, 100), color=255)
        img_path = tmp_path / "test.png"
        img.save(img_path)

        mock_spi.set_read_data([0])
        initialized_display.display_image(img_path, x=0, y=0)

    def test_display_image_from_bytes(
        self, initialized_display: EPaperDisplay, mock_spi: MockSPI
    ) -> None:
        """Test displaying image from bytes buffer."""
        img = Image.new("L", (100, 100), color=0)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        mock_spi.set_read_data([0])
        initialized_display.display_image(buffer, x=0, y=0)

    def test_display_image_validation(self, initialized_display: EPaperDisplay) -> None:
        """Test image display validation."""
        img = Image.new("L", (2000, 100))

        with pytest.raises(InvalidParameterError) as exc_info:
            initialized_display.display_image(img, x=0, y=0)

        assert "exceeds display width" in str(exc_info.value)

        img = Image.new("L", (100, 1000))
        with pytest.raises(InvalidParameterError) as exc_info:
            initialized_display.display_image(img, x=0, y=700)

        assert "exceeds display height" in str(exc_info.value)

    def test_display_image_rotation(
        self, initialized_display: EPaperDisplay, mock_spi: MockSPI
    ) -> None:
        """Test image rotation."""
        img = Image.new("L", (200, 100), color=64)
        mock_spi.set_read_data([0])

        initialized_display.display_image(img, rotation=Rotation.ROTATE_90)

        img2 = Image.new("L", (100, 200), color=64)
        mock_spi.set_read_data([0])
        initialized_display.display_image(img2, rotation=Rotation.ROTATE_180)

    def test_display_partial(self, initialized_display: EPaperDisplay, mock_spi: MockSPI) -> None:
        """Test partial display update."""
        img = Image.new("L", (100, 100), color=200)
        mock_spi.set_read_data([0])

        initialized_display.display_partial(img, x=100, y=100, mode=DisplayMode.DU)

        arr = (np.ones((100, 100), dtype=np.uint8) * 128).astype(np.uint8)
        mock_spi.set_read_data([0])
        initialized_display.display_partial(arr, x=200, y=200)

        arr_float = np.ones((100, 100), dtype=np.float32) * 0.5
        mock_spi.set_read_data([0])
        initialized_display.display_partial(arr_float, x=300, y=300)  # type: ignore[arg-type]

    def test_vcom_operations(self, initialized_display: EPaperDisplay, mock_spi: MockSPI) -> None:
        """Test VCOM operations."""
        initialized_display.set_vcom(-3.0)

        mock_spi.set_read_data([3000])
        voltage = initialized_display.get_vcom()
        assert voltage == -3.0

    def test_power_operations(self, initialized_display: EPaperDisplay) -> None:
        """Test power operations."""
        initialized_display.sleep()
        initialized_display.standby()

    def test_properties(self, initialized_display: EPaperDisplay) -> None:
        """Test display properties."""
        assert initialized_display.width == 1024
        assert initialized_display.height == 768
        assert initialized_display.size == (1024, 768)

    def test_properties_without_init(self, display: EPaperDisplay) -> None:
        """Test properties raise error without initialization."""
        with pytest.raises(DisplayError):
            _ = display.width

        with pytest.raises(DisplayError):
            _ = display.height

        with pytest.raises(DisplayError):
            _ = display.size

    def test_operations_without_init(self, display: EPaperDisplay) -> None:
        """Test operations fail without initialization."""
        with pytest.raises(DisplayError):
            display.clear()

        with pytest.raises(DisplayError):
            display.display_image(Image.new("L", (100, 100)))

        with pytest.raises(DisplayError):
            display.set_vcom(-2.0)

    def test_image_alignment(self, initialized_display: EPaperDisplay, mock_spi: MockSPI) -> None:
        """Test image coordinate and dimension alignment."""
        img = Image.new("L", (99, 99), color=128)
        mock_spi.set_read_data([0])

        initialized_display.display_image(img, x=1, y=2)

        buffer = mock_spi.get_data_buffer()
        assert 0 in buffer
        assert 100 in buffer

    def test_invalid_image_source(self, initialized_display: EPaperDisplay) -> None:
        """Test invalid image source handling."""
        with pytest.raises(InvalidParameterError) as exc_info:
            initialized_display.display_image(12345)  # type: ignore[arg-type]

        assert "Invalid image source" in str(exc_info.value)

    def test_rgb_to_grayscale_conversion(
        self, initialized_display: EPaperDisplay, mock_spi: MockSPI
    ) -> None:
        """Test RGB image is converted to grayscale."""
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        mock_spi.set_read_data([0])

        initialized_display.display_image(img)

        assert mock_spi.get_data_buffer()

    def test_memory_error_oversized_image(self, mocker: MockerFixture) -> None:
        """Test IT8951MemoryError for oversized images."""
        mock_spi = MockSPI()
        display = EPaperDisplay(spi_interface=mock_spi)

        # Mock initialization
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])

        # Mock _wait_display_ready to avoid timeouts in tests
        mocker.patch.object(display._controller, "_wait_display_ready")  # type: ignore[union-attr]

        display.init()

        # Create an image that exceeds max dimensions
        oversized_img = Image.new("L", (3000, 3000), color=128)

        with pytest.raises(IT8951MemoryError) as exc_info:
            display.display_image(oversized_img)

        assert "exceed maximum" in str(exc_info.value)
        assert "2048x2048" in str(exc_info.value)

    def test_memory_error_buffer_allocation(self, mocker: MockerFixture) -> None:
        """Test IT8951MemoryError when buffer allocation fails."""
        mock_spi = MockSPI()
        display = EPaperDisplay(spi_interface=mock_spi)

        # Mock initialization with regular display size
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])

        # Mock _wait_display_ready to avoid timeouts in tests
        mocker.patch.object(display._controller, "_wait_display_ready")  # type: ignore[union-attr]

        display.init()

        # Mock bytes() to raise MemoryError
        mocker.patch("builtins.bytes", side_effect=MemoryError("Out of memory"))

        with pytest.raises(IT8951MemoryError) as exc_info:
            display.clear()

        assert "Failed to allocate display buffer" in str(exc_info.value)

    def test_enhanced_driving_init(
        self, enhanced_display: EPaperDisplay, mock_spi: MockSPI
    ) -> None:
        """Test that enhanced driving is applied during initialization."""
        # Verify that enhance_driving_capability was called
        # We need to check the buffer for the register write
        buffer = mock_spi.get_data_buffer()

        # Import constants for the test
        from IT8951_ePaper_Py.constants import ProtocolConstants, Register

        # Verify enhanced driving register was written
        assert Register.ENHANCE_DRIVING in buffer
        assert ProtocolConstants.ENHANCED_DRIVING_VALUE in buffer

        # Verify display still initializes correctly
        assert enhanced_display.width == 1024
        assert enhanced_display.height == 768

    def test_align_coordinate_default(self, display: EPaperDisplay) -> None:
        """Test coordinate alignment with default pixel format."""
        # Test alignment to 4-pixel boundary (default)
        assert display._align_coordinate(0) == 0
        assert display._align_coordinate(1) == 0
        assert display._align_coordinate(3) == 0
        assert display._align_coordinate(4) == 4
        assert display._align_coordinate(5) == 4
        assert display._align_coordinate(7) == 4
        assert display._align_coordinate(8) == 8
        assert display._align_coordinate(100) == 100
        assert display._align_coordinate(101) == 100

    def test_align_coordinate_1bpp(self, display: EPaperDisplay) -> None:
        """Test coordinate alignment with 1bpp pixel format."""
        from IT8951_ePaper_Py.constants import PixelFormat

        # Test alignment to 32-pixel boundary for 1bpp
        assert display._align_coordinate(0, PixelFormat.BPP_1) == 0
        assert display._align_coordinate(1, PixelFormat.BPP_1) == 0
        assert display._align_coordinate(31, PixelFormat.BPP_1) == 0
        assert display._align_coordinate(32, PixelFormat.BPP_1) == 32
        assert display._align_coordinate(33, PixelFormat.BPP_1) == 32
        assert display._align_coordinate(63, PixelFormat.BPP_1) == 32
        assert display._align_coordinate(64, PixelFormat.BPP_1) == 64
        assert display._align_coordinate(100, PixelFormat.BPP_1) == 96
        assert display._align_coordinate(128, PixelFormat.BPP_1) == 128

    def test_align_dimension_default(self, display: EPaperDisplay) -> None:
        """Test dimension alignment with default pixel format."""
        # Test alignment to 4-pixel multiple (default)
        assert display._align_dimension(0) == 0
        assert display._align_dimension(1) == 4
        assert display._align_dimension(3) == 4
        assert display._align_dimension(4) == 4
        assert display._align_dimension(5) == 8
        assert display._align_dimension(7) == 8
        assert display._align_dimension(8) == 8
        assert display._align_dimension(100) == 100
        assert display._align_dimension(101) == 104

    def test_align_dimension_1bpp(self, display: EPaperDisplay) -> None:
        """Test dimension alignment with 1bpp pixel format."""
        from IT8951_ePaper_Py.constants import PixelFormat

        # Test alignment to 32-pixel multiple for 1bpp
        assert display._align_dimension(0, PixelFormat.BPP_1) == 0
        assert display._align_dimension(1, PixelFormat.BPP_1) == 32
        assert display._align_dimension(31, PixelFormat.BPP_1) == 32
        assert display._align_dimension(32, PixelFormat.BPP_1) == 32
        assert display._align_dimension(33, PixelFormat.BPP_1) == 64
        assert display._align_dimension(63, PixelFormat.BPP_1) == 64
        assert display._align_dimension(64, PixelFormat.BPP_1) == 64
        assert display._align_dimension(100, PixelFormat.BPP_1) == 128
        assert display._align_dimension(128, PixelFormat.BPP_1) == 128

    def test_validate_alignment_default(self, display: EPaperDisplay) -> None:
        """Test alignment validation with default pixel format."""
        # Aligned values should pass
        is_valid, warnings = display.validate_alignment(0, 0, 100, 100)
        assert is_valid
        assert len(warnings) == 0

        # Unaligned X coordinate
        is_valid, warnings = display.validate_alignment(1, 0, 100, 100)
        assert not is_valid
        assert len(warnings) == 1
        assert "X coordinate 1 not aligned to 4-pixel boundary" in warnings[0]

        # Multiple unaligned values
        is_valid, warnings = display.validate_alignment(1, 2, 101, 102)
        assert not is_valid
        assert len(warnings) == 4

    def test_validate_alignment_1bpp(self, display: EPaperDisplay) -> None:
        """Test alignment validation with 1bpp pixel format."""
        from IT8951_ePaper_Py.constants import PixelFormat

        # Aligned values should pass
        is_valid, warnings = display.validate_alignment(0, 0, 64, 64, PixelFormat.BPP_1)
        assert is_valid
        assert len(warnings) == 0

        # Unaligned values for 1bpp
        is_valid, warnings = display.validate_alignment(16, 16, 100, 100, PixelFormat.BPP_1)
        assert not is_valid
        assert len(warnings) == 5  # 4 alignment warnings + 1 special 1bpp note
        assert "1bpp mode requires strict 32-pixel alignment" in warnings[0]
        assert "X coordinate 16 not aligned to 32-pixel (4-byte) boundary" in warnings[1]

    def test_display_image_with_alignment_warnings(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test that display_image generates alignment warnings."""
        from IT8951_ePaper_Py.constants import PixelFormat

        # Create a test image with unaligned dimensions
        img = Image.new("L", (33, 33), color=128)

        # Mock pack_pixels to avoid implementation
        mocker.patch.object(
            initialized_display._controller, "pack_pixels", return_value=b"\x00" * (64 * 64)
        )

        # Mock the controller methods to avoid timeout
        mocker.patch.object(initialized_display._controller, "load_image_area_start")
        mocker.patch.object(initialized_display._controller, "load_image_write")
        mocker.patch.object(initialized_display._controller, "load_image_end")
        mocker.patch.object(initialized_display._controller, "display_area")

        # Mock warnings module to capture warnings
        mock_warn = mocker.patch("warnings.warn")

        # Display with 1bpp format to trigger alignment warnings
        initialized_display.display_image(img, x=1, y=1, pixel_format=PixelFormat.BPP_1)

        # Check that warnings were issued
        assert mock_warn.call_count > 0
        warning_messages = [call[0][0] for call in mock_warn.call_args_list]

        # Verify specific warnings
        assert any(
            "1bpp mode requires strict 32-pixel alignment" in msg for msg in warning_messages
        )
        assert any("X coordinate 1 not aligned" in msg for msg in warning_messages)

    def test_requires_special_1bpp_alignment(self, initialized_display: EPaperDisplay) -> None:
        """Test model detection for 1bpp alignment requirements."""
        # Currently always returns True (conservative approach)
        assert initialized_display._requires_special_1bpp_alignment() is True

        # Test with no device info (before init)
        display = EPaperDisplay(spi_interface=MockSPI())
        assert display._requires_special_1bpp_alignment() is True

    def test_dump_registers(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test register dump functionality."""
        # Mock the controller's dump_registers method
        mock_registers = {
            "LISAR": 0x1234,
            "REG_0204": 0x5678,
            "MISC": 0x9ABC,
            "ENHANCE_DRIVING": 0x0602,
        }
        mocker.patch.object(
            initialized_display._controller, "dump_registers", return_value=mock_registers
        )

        # Call dump_registers
        registers = initialized_display.dump_registers()

        # Verify the result
        assert registers == mock_registers
        assert registers["ENHANCE_DRIVING"] == 0x0602


class TestA2ModeAutoClearing:
    """Test A2 mode auto-clear protection functionality."""

    @pytest.fixture
    def display_with_a2_limit(self, mocker: MockerFixture) -> EPaperDisplay:
        """Create display with A2 refresh limit."""
        mock_spi = MockSPI()
        display = EPaperDisplay(spi_interface=mock_spi, a2_refresh_limit=5)

        # Mock initialization
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mocker.patch.object(display, "clear")

        # Mock _wait_display_ready to avoid timeouts in tests
        mocker.patch.object(display._controller, "_wait_display_ready")

        display.init()
        return display

    def test_a2_counter_increments(self, display_with_a2_limit: EPaperDisplay) -> None:
        """Test A2 refresh counter increments correctly."""
        display = display_with_a2_limit
        assert display.a2_refresh_count == 0

        # Create test image
        img = Image.new("L", (100, 100), color=128)

        # Display with A2 mode
        display.display_image(img, mode=DisplayMode.A2)
        assert display.a2_refresh_count == 1

        display.display_image(img, mode=DisplayMode.A2)
        assert display.a2_refresh_count == 2

    def test_non_a2_mode_doesnt_increment(self, display_with_a2_limit: EPaperDisplay) -> None:
        """Test non-A2 modes don't increment counter."""
        display = display_with_a2_limit
        img = Image.new("L", (100, 100), color=128)

        display.display_image(img, mode=DisplayMode.GC16)
        assert display.a2_refresh_count == 0

        display.display_image(img, mode=DisplayMode.DU)
        assert display.a2_refresh_count == 0

    def test_warning_before_limit(self, display_with_a2_limit: EPaperDisplay) -> None:
        """Test warning is issued before reaching limit."""
        display = display_with_a2_limit
        img = Image.new("L", (100, 100), color=128)

        # Get to 3 refreshes (next one will be the 4th, which triggers warning)
        for _ in range(3):
            display.display_image(img, mode=DisplayMode.A2)

        # 4th refresh should trigger warning (count goes from 3 to 4, limit-1)
        with pytest.warns(UserWarning, match="A2 refresh count .* approaching limit"):
            display.display_image(img, mode=DisplayMode.A2)

    def test_auto_clear_at_limit(self, display_with_a2_limit: EPaperDisplay) -> None:
        """Test auto-clear triggers at limit."""
        display = display_with_a2_limit
        img = Image.new("L", (100, 100), color=128)

        # Reset the clear mock to track calls
        display.clear.reset_mock()  # type: ignore[attr-defined]

        # Get to limit-1 (4 refreshes)
        for _ in range(4):
            display.display_image(img, mode=DisplayMode.A2)

        # Should not have cleared yet
        display.clear.assert_not_called()  # type: ignore[attr-defined]
        assert display.a2_refresh_count == 4

        # 5th refresh should trigger clear (reaches limit)
        display.display_image(img, mode=DisplayMode.A2)
        display.clear.assert_called_once()  # type: ignore[attr-defined]
        assert display.a2_refresh_count == 0

    def test_manual_clear_resets_counter(self, mocker: MockerFixture) -> None:
        """Test manual clear resets A2 counter."""
        mock_spi = MockSPI()
        display = EPaperDisplay(spi_interface=mock_spi, a2_refresh_limit=10)

        # Mock initialization
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])

        # Mock _wait_display_ready to avoid timeouts in tests
        mocker.patch.object(display._controller, "_wait_display_ready")

        display.init()

        # Set up some A2 refreshes
        img = Image.new("L", (100, 100), color=128)
        for _ in range(3):
            display.display_image(img, mode=DisplayMode.A2)

        assert display.a2_refresh_count == 3

        # Manual clear should reset counter
        display.clear()
        assert display.a2_refresh_count == 0

    def test_disabled_auto_clear(self, mocker: MockerFixture) -> None:
        """Test auto-clear can be disabled."""
        mock_spi = MockSPI()
        display = EPaperDisplay(spi_interface=mock_spi, a2_refresh_limit=0)

        # Mock initialization
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_clear = mocker.patch.object(display, "clear")

        # Mock _wait_display_ready to avoid timeouts in tests
        mocker.patch.object(display._controller, "_wait_display_ready")

        display.init()

        # Many A2 refreshes should not trigger clear
        img = Image.new("L", (100, 100), color=128)
        for _ in range(20):
            display.display_image(img, mode=DisplayMode.A2)
            assert display.a2_refresh_count == 0  # Counter stays at 0 when disabled

        # Clear should not have been called
        mock_clear.assert_called_once()  # Only during init

    def test_properties(self) -> None:
        """Test A2 refresh properties."""
        display = EPaperDisplay(a2_refresh_limit=7)

        assert display.a2_refresh_count == 0
        assert display.a2_refresh_limit == 7

        # Test with disabled auto-clear
        display2 = EPaperDisplay(a2_refresh_limit=0)
        assert display2.a2_refresh_limit == 0
