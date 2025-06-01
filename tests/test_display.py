"""Tests for high-level display interface."""

import io
import warnings
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from pytest_mock import MockerFixture

from IT8951_ePaper_Py.alignment import align_coordinate, align_dimension, validate_alignment
from IT8951_ePaper_Py.constants import DisplayMode, MemoryConstants, PixelFormat, Rotation
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
        return EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

    @pytest.fixture
    def initialized_display(
        self, display: EPaperDisplay, mock_spi: MockSPI, mocker: MockerFixture
    ) -> EPaperDisplay:
        """Create and initialize EPaperDisplay."""
        # Data for _get_device_info (20 values)
        mock_spi.set_read_data(
            [
                1024,  # panel_width
                768,  # panel_height
                MemoryConstants.IMAGE_BUFFER_ADDR_L,  # memory_addr_l
                MemoryConstants.IMAGE_BUFFER_ADDR_H,  # memory_addr_h
                49,
                46,
                48,
                0,
                0,
                0,
                0,
                0,  # fw_version "1.0"
                50,
                46,
                48,
                0,
                0,
                0,
                0,
                0,  # lut_version "2.0"
            ]
        )
        # Data for _enable_packed_write register read
        mock_spi.set_read_data([0x0000])

        # Data for get_vcom() call in init() - return 2000 (2.0V)
        mock_spi.set_read_data([2000])

        # Mock clear to avoid complex setup
        mocker.patch.object(display, "clear")

        display.init()
        return display

    @pytest.fixture
    def enhanced_display(self, mock_spi: MockSPI, mocker: MockerFixture) -> EPaperDisplay:
        """Create EPaperDisplay with enhanced driving enabled."""
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi, enhance_driving=True)

        # Data for _get_device_info (20 values)
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        # Data for _enable_packed_write register read
        mock_spi.set_read_data([0x0000])

        # Data for get_vcom() call in init() - return 2000 (2.0V)
        mock_spi.set_read_data([2000])

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

        # Data for get_vcom() call in init() - return 2000 (2.0V)
        mock_spi.set_read_data([2000])

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

        assert "exceeds panel width" in str(exc_info.value)

        img = Image.new("L", (100, 1000))
        with pytest.raises(InvalidParameterError) as exc_info:
            initialized_display.display_image(img, x=0, y=700)

        assert "exceeds panel height" in str(exc_info.value)

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
        # Add read data for get_vcom() call after set_vcom()
        mock_spi.set_read_data([3000])
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
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

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
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Mock initialization with regular display size
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])

        # Mock _wait_display_ready to avoid timeouts in tests
        mocker.patch.object(display._controller, "_wait_display_ready")  # type: ignore[union-attr]

        display.init()

        # Mock ManagedBuffer.bytes to raise MemoryError instead of mocking global bytes()
        # This is safer for parallel test execution
        mocker.patch(
            "IT8951_ePaper_Py.buffer_pool.ManagedBuffer.bytes",
            side_effect=MemoryError("Out of memory"),
        )

        with pytest.raises(IT8951MemoryError) as exc_info:
            display.clear()

        assert "Failed to allocate display buffer" in str(exc_info.value)

    def test_memory_usage_warning(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test memory usage warning for large images."""
        # Mock wait_display_ready to avoid timeout
        mocker.patch.object(initialized_display._controller, "_wait_display_ready")

        # Mock the WARNING_THRESHOLD_BYTES to a lower value for testing
        # Display is 1024x768, so create max size image for this display
        # 1024x768 at 8bpp = 786KB, need to lower threshold for test
        mocker.patch.object(MemoryConstants, "WARNING_THRESHOLD_BYTES", 512 * 1024)

        # Create 1024x768 image (786KB at 8bpp)
        img = Image.new("L", (1024, 768))

        with pytest.warns(UserWarning, match="Large image memory usage"):
            initialized_display.display_image(img, pixel_format=PixelFormat.BPP_8)

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
        assert align_coordinate(0) == 0
        assert align_coordinate(1) == 0
        assert align_coordinate(3) == 0
        assert align_coordinate(4) == 4
        assert align_coordinate(5) == 4
        assert align_coordinate(7) == 4
        assert align_coordinate(8) == 8
        assert align_coordinate(100) == 100
        assert align_coordinate(101) == 100

    def test_align_coordinate_1bpp(self, display: EPaperDisplay) -> None:
        """Test coordinate alignment with 1bpp pixel format."""
        from IT8951_ePaper_Py.constants import PixelFormat

        # Test alignment to 32-pixel boundary for 1bpp
        assert align_coordinate(0, PixelFormat.BPP_1) == 0
        assert align_coordinate(1, PixelFormat.BPP_1) == 0
        assert align_coordinate(31, PixelFormat.BPP_1) == 0
        assert align_coordinate(32, PixelFormat.BPP_1) == 32
        assert align_coordinate(33, PixelFormat.BPP_1) == 32
        assert align_coordinate(63, PixelFormat.BPP_1) == 32
        assert align_coordinate(64, PixelFormat.BPP_1) == 64
        assert align_coordinate(100, PixelFormat.BPP_1) == 96
        assert align_coordinate(128, PixelFormat.BPP_1) == 128

    def test_align_dimension_default(self, display: EPaperDisplay) -> None:
        """Test dimension alignment with default pixel format."""
        # Test alignment to 4-pixel multiple (default)
        assert align_dimension(0) == 0
        assert align_dimension(1) == 4
        assert align_dimension(3) == 4
        assert align_dimension(4) == 4
        assert align_dimension(5) == 8
        assert align_dimension(7) == 8
        assert align_dimension(8) == 8
        assert align_dimension(100) == 100
        assert align_dimension(101) == 104

    def test_align_dimension_1bpp(self, display: EPaperDisplay) -> None:
        """Test dimension alignment with 1bpp pixel format."""
        from IT8951_ePaper_Py.constants import PixelFormat

        # Test alignment to 32-pixel multiple for 1bpp
        assert align_dimension(0, PixelFormat.BPP_1) == 0
        assert align_dimension(1, PixelFormat.BPP_1) == 32
        assert align_dimension(31, PixelFormat.BPP_1) == 32
        assert align_dimension(32, PixelFormat.BPP_1) == 32
        assert align_dimension(33, PixelFormat.BPP_1) == 64
        assert align_dimension(63, PixelFormat.BPP_1) == 64
        assert align_dimension(64, PixelFormat.BPP_1) == 64
        assert align_dimension(100, PixelFormat.BPP_1) == 128
        assert align_dimension(128, PixelFormat.BPP_1) == 128

    def test_validate_alignment_default(self, display: EPaperDisplay) -> None:
        """Test alignment validation with default pixel format."""
        # Aligned values should pass
        is_valid, warnings = validate_alignment(0, 0, 100, 100)
        assert is_valid
        assert len(warnings) == 0

        # Unaligned X coordinate
        is_valid, warnings = validate_alignment(1, 0, 100, 100)
        assert not is_valid
        assert len(warnings) == 1
        assert "X coordinate 1 not aligned to 4-pixel boundary" in warnings[0]

        # Multiple unaligned values
        is_valid, warnings = validate_alignment(1, 2, 101, 102)
        assert not is_valid
        assert len(warnings) == 4

    def test_validate_alignment_1bpp(self, display: EPaperDisplay) -> None:
        """Test alignment validation with 1bpp pixel format."""
        from IT8951_ePaper_Py.constants import PixelFormat

        # Aligned values should pass
        is_valid, warnings = validate_alignment(0, 0, 64, 64, PixelFormat.BPP_1)
        assert is_valid
        assert len(warnings) == 0

        # Unaligned values for 1bpp
        is_valid, warnings = validate_alignment(16, 16, 100, 100, PixelFormat.BPP_1)
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
        display = EPaperDisplay(vcom=-2.0, spi_interface=MockSPI())
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

    def test_vcom_calibration_helper(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test the find_optimal_vcom() method."""
        # Mock user inputs for the calibration process
        mock_input = mocker.patch("builtins.input")
        mock_input.side_effect = ["", "", "select"]  # Two nexts, then select

        # Mock time.sleep to speed up tests
        mocker.patch("time.sleep")

        # Mock the display operations
        mock_clear = mocker.patch.object(initialized_display, "clear")
        mock_display_image = mocker.patch.object(initialized_display, "display_image")
        mock_set_vcom = mocker.patch.object(initialized_display, "set_vcom")

        # Run calibration
        result = initialized_display.find_optimal_vcom(
            start_voltage=-2.5, end_voltage=-1.5, step=0.5
        )

        # Should have selected -1.5V (after two steps)
        assert result == -1.5

        # Verify operations were called
        assert mock_clear.call_count == 3  # Once for each voltage tested
        assert mock_display_image.call_count == 3
        assert mock_set_vcom.call_count == 3

    def test_vcom_calibration_quit(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test quitting the VCOM calibration."""
        mocker.patch("builtins.input", return_value="quit")
        mocker.patch("time.sleep")
        mocker.patch.object(initialized_display, "clear")
        mocker.patch.object(initialized_display, "display_image")
        mocker.patch.object(initialized_display, "set_vcom")

        result = initialized_display.find_optimal_vcom()

        # Should return the current VCOM when quit
        assert result == initialized_display._vcom

    def test_vcom_calibration_back(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test going back in VCOM calibration."""
        mock_input = mocker.patch("builtins.input")
        mock_input.side_effect = ["", "back", "select"]  # Next, back, select

        mocker.patch("time.sleep")
        mocker.patch.object(initialized_display, "clear")
        mocker.patch.object(initialized_display, "display_image")
        mock_set_vcom = mocker.patch.object(initialized_display, "set_vcom")

        result = initialized_display.find_optimal_vcom(
            start_voltage=-3.0, end_voltage=-1.0, step=1.0
        )

        # Should select -3.0V (went to -2.0, then back to -3.0)
        assert result == -3.0

        # Check VCOM was set in correct order
        vcom_calls = [call[0][0] for call in mock_set_vcom.call_args_list]
        assert vcom_calls == [-3.0, -2.0, -3.0]  # Initial, next, back

    def test_vcom_calibration_invalid_range(self, initialized_display: EPaperDisplay) -> None:
        """Test VCOM calibration with invalid voltage range."""
        from IT8951_ePaper_Py.exceptions import VCOMError

        # Test with voltage out of range
        with pytest.raises(VCOMError, match="Voltage range must be between"):
            initialized_display.find_optimal_vcom(
                start_voltage=-6.0,  # Below minimum
                end_voltage=-1.0,
            )

    def test_vcom_calibration_swapped_range(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test VCOM calibration with swapped start/end voltages."""
        mocker.patch("builtins.input", return_value="select")
        mocker.patch("time.sleep")
        mocker.patch.object(initialized_display, "clear")
        mocker.patch.object(initialized_display, "display_image")
        mocker.patch.object(initialized_display, "set_vcom")

        # Swap start and end - should still work
        result = initialized_display.find_optimal_vcom(
            start_voltage=-1.0,  # Higher than end
            end_voltage=-3.0,  # Lower than start
            step=0.5,
        )

        assert result == -3.0  # Should start from the lower voltage

    def test_vcom_calibration_custom_pattern(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test VCOM calibration with custom test pattern."""
        mocker.patch("builtins.input", return_value="select")
        mocker.patch("time.sleep")
        mocker.patch.object(initialized_display, "clear")
        mock_display_image = mocker.patch.object(initialized_display, "display_image")
        mocker.patch.object(initialized_display, "set_vcom")

        # Create custom pattern
        custom_pattern = Image.new("L", (200, 200), color=128)

        initialized_display.find_optimal_vcom(test_pattern=custom_pattern)

        # Verify custom pattern was used
        call_args = mock_display_image.call_args[0][0]
        assert call_args is custom_pattern

    def test_vcom_calibration_end_of_range(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test VCOM calibration reaching end of range."""
        mock_input = mocker.patch("builtins.input")
        # Keep pressing enter until end of range, then select
        mock_input.side_effect = ["", "", "", "", "select"]

        mock_print = mocker.patch("builtins.print")
        mocker.patch("time.sleep")
        mocker.patch.object(initialized_display, "clear")
        mocker.patch.object(initialized_display, "display_image")
        mocker.patch.object(initialized_display, "set_vcom")

        result = initialized_display.find_optimal_vcom(
            start_voltage=-2.0, end_voltage=-1.0, step=0.5
        )

        # Should stay at -1.0 after reaching end
        assert result == -1.0

        # Check that end of range message was printed
        print_calls = [str(call[0][0]) for call in mock_print.call_args_list]
        assert any("Reached end of range" in msg for msg in print_calls)

    def test_create_vcom_test_pattern(self, display: EPaperDisplay) -> None:
        """Test the VCOM test pattern creation."""
        from IT8951_ePaper_Py.vcom_calibration import create_default_test_pattern

        pattern = create_default_test_pattern(256, 128)

        assert isinstance(pattern, Image.Image)
        assert pattern.size == (256, 128)
        assert pattern.mode == "L"

        # Check that it has gradients (different pixel values)
        pixels = list(pattern.getdata())
        unique_values = set(pixels)
        assert len(unique_values) > 1  # Should have multiple gray levels

    def test_vcom_mismatch_warning(
        self, initialized_display: EPaperDisplay, mock_spi: MockSPI, mocker: MockerFixture
    ) -> None:
        """Test VCOM mismatch detection in set_vcom."""
        # Mock get_vcom to return a different value than what was set
        mock_spi.set_read_data([2100])  # Returns -2.1V

        mock_warn = mocker.patch("warnings.warn")

        # Set VCOM to -2.0V but device returns -2.1V
        initialized_display.set_vcom(-2.0)

        # Should have warned about mismatch
        mock_warn.assert_called_once()
        warning_msg = mock_warn.call_args[0][0]
        assert "VCOM mismatch after setting" in warning_msg
        assert "Requested: -2.0V" in warning_msg
        assert "Actual: -2.1V" in warning_msg

        # Internal VCOM should be updated to actual value
        assert initialized_display._vcom == -2.1

    def test_vcom_no_mismatch(
        self, initialized_display: EPaperDisplay, mock_spi: MockSPI, mocker: MockerFixture
    ) -> None:
        """Test VCOM setting without mismatch."""
        # Mock get_vcom to return the same value
        mock_spi.set_read_data([2000])  # Returns -2.0V

        mock_warn = mocker.patch("warnings.warn")

        # Set VCOM to -2.0V and device returns -2.0V
        initialized_display.set_vcom(-2.0)

        # Should not warn
        assert mock_warn.call_count == 0

        # Internal VCOM should be the requested value
        assert initialized_display._vcom == -2.0

    def test_close_with_controller(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test that close() properly cleans up the controller."""
        # Mock the controller's close method
        mock_controller_close = mocker.patch.object(initialized_display._controller, "close")

        # Close the display
        initialized_display.close()

        # Verify controller was closed
        mock_controller_close.assert_called_once()

        # Verify initialized flag is cleared
        assert not initialized_display._initialized

    def test_clear_memory_allocation_edge_case(self, mocker: MockerFixture) -> None:
        """Test clear() with display size at maximum."""
        mock_spi = MockSPI()
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Mock initialization with maximum allowed display size
        mock_spi.set_read_data(
            [2048, 2048, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])  # VCOM

        mocker.patch.object(display._controller, "_wait_display_ready")

        # Patch the clear method to simulate behavior
        # Since we're testing the check in clear(), we need to mock the display
        # to have oversized dimensions
        display.init()

        # Manually set width/height to exceed maximum after initialization
        display._width = 3000
        display._height = 3000

        # Attempting to clear should raise memory error
        with pytest.raises(IT8951MemoryError, match="exceeds maximum"):
            display.clear()

    def test_prepare_image_all_rotations(self, display: EPaperDisplay) -> None:
        """Test all rotation cases in _prepare_image."""
        # Create a non-square image to verify rotation
        img = Image.new("L", (100, 200), color=128)

        # Test 0 degrees (no rotation)
        rotated = display._prepare_image(img, Rotation.ROTATE_0)
        assert rotated.size == (100, 200)

        # Test 90 degrees
        rotated = display._prepare_image(img, Rotation.ROTATE_90)
        assert rotated.size == (200, 100)  # Width and height swapped

        # Test 180 degrees
        rotated = display._prepare_image(img, Rotation.ROTATE_180)
        assert rotated.size == (100, 200)  # Same size

        # Test 270 degrees
        rotated = display._prepare_image(img, Rotation.ROTATE_270)
        assert rotated.size == (200, 100)  # Width and height swapped

    def test_is_enhanced_driving_enabled(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test the is_enhanced_driving_enabled method."""
        # Mock the controller's method
        mock_is_enabled = mocker.patch.object(
            initialized_display._controller, "is_enhanced_driving_enabled", return_value=True
        )

        result = initialized_display.is_enhanced_driving_enabled()

        assert result is True
        mock_is_enabled.assert_called_once()

    def test_display_image_with_different_pixel_formats(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test display_image with various pixel formats."""
        from IT8951_ePaper_Py.constants import PixelFormat

        img = Image.new("L", (64, 64), color=128)

        # Mock the controller methods
        mocker.patch.object(
            initialized_display._controller, "pack_pixels", return_value=b"\x00" * 1000
        )
        mocker.patch.object(initialized_display._controller, "load_image_area_start")
        mocker.patch.object(initialized_display._controller, "load_image_write")
        mocker.patch.object(initialized_display._controller, "load_image_end")
        mocker.patch.object(initialized_display._controller, "display_area")

        # Test with different pixel formats
        for pixel_format in [
            PixelFormat.BPP_1,
            PixelFormat.BPP_2,
            PixelFormat.BPP_4,
            PixelFormat.BPP_8,
        ]:
            initialized_display.display_image(img, pixel_format=pixel_format)

    def test_vcom_error_propagation(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test that VCOMError from controller is properly propagated."""
        from IT8951_ePaper_Py.exceptions import VCOMError

        # Mock set_vcom to raise VCOMError
        mocker.patch.object(
            initialized_display._controller, "set_vcom", side_effect=VCOMError("Invalid VCOM")
        )

        with pytest.raises(VCOMError, match="Invalid VCOM"):
            initialized_display.set_vcom(-6.0)

    def test_load_image_from_path_string(
        self, initialized_display: EPaperDisplay, tmp_path: Path
    ) -> None:
        """Test _load_image with string path."""
        img = Image.new("L", (100, 100), color=255)
        img_path = tmp_path / "test.png"
        img.save(img_path)

        # Test with string path
        loaded_img = initialized_display._load_image(str(img_path))
        assert isinstance(loaded_img, Image.Image)
        assert loaded_img.mode == "L"
        assert loaded_img.size == (100, 100)

    def test_get_device_status(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test get_device_status method."""
        from IT8951_ePaper_Py.constants import PowerState

        # Mock enhanced driving check
        mocker.patch.object(initialized_display, "is_enhanced_driving_enabled", return_value=True)

        # Set some test values
        initialized_display._a2_refresh_count = 5
        initialized_display.set_auto_sleep_timeout(30.0)

        # Get device status
        status = initialized_display.get_device_status()

        # Verify device info fields
        assert status["panel_width"] == 1024
        assert status["panel_height"] == 768
        # Check memory address is a hex string
        mem_addr = status["memory_address"]
        assert isinstance(mem_addr, str)
        assert mem_addr.startswith("0x")
        assert status["fw_version"] == "1.0"
        assert status["lut_version"] == "2.0"

        # Verify runtime status fields
        assert status["power_state"] == PowerState.ACTIVE.name
        assert status["vcom_voltage"] == -2.0
        assert status["a2_refresh_count"] == 5
        assert status["a2_refresh_limit"] == 10
        assert status["auto_sleep_timeout"] == 30.0
        assert status["enhanced_driving"] is True

    def test_create_display_without_spi_interface(self, mocker: MockerFixture) -> None:
        """Test creating EPaperDisplay without providing spi_interface."""
        # Mock the create_spi_interface function
        mock_spi = MockSPI()
        mock_create_spi = mocker.patch(
            "IT8951_ePaper_Py.display.create_spi_interface", return_value=mock_spi
        )

        # Create display without spi_interface
        display = EPaperDisplay(vcom=-2.0, spi_speed_hz=10000000)

        # Verify create_spi_interface was called with the speed
        mock_create_spi.assert_called_once_with(spi_speed_hz=10000000)

        # Verify the display was created with the mocked SPI
        assert display._controller._spi == mock_spi

    def test_display_image_progressive(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test progressive image display for large images."""
        # Create a test image
        img = Image.new("L", (512, 512), color=128)

        # Mock the controller methods
        mocker.patch.object(
            initialized_display._controller, "pack_pixels", return_value=b"\x00" * 1000
        )
        mock_load_start = mocker.patch.object(
            initialized_display._controller, "load_image_area_start"
        )
        mock_load_write = mocker.patch.object(initialized_display._controller, "load_image_write")
        mock_load_end = mocker.patch.object(initialized_display._controller, "load_image_end")
        mock_display_area = mocker.patch.object(initialized_display._controller, "display_area")

        # Display image progressively with 128-pixel chunks
        initialized_display.display_image_progressive(img, chunk_height=128)

        # Should have been called 4 times (512 / 128 = 4 chunks)
        assert mock_load_start.call_count == 4
        assert mock_load_write.call_count == 4
        assert mock_load_end.call_count == 4
        assert mock_display_area.call_count == 4

        # Check that chunks were displayed at correct Y positions
        y_positions = [call[0][0].y for call in mock_display_area.call_args_list]
        assert y_positions == [0, 128, 256, 384]

    def test_display_image_progressive_with_1bpp_alignment(
        self, initialized_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test progressive display with 1bpp alignment requirements."""
        from IT8951_ePaper_Py.constants import PixelFormat

        # Create test image with size that doesn't align to 32 pixels
        img = Image.new("L", (100, 100), color=255)

        # Mock the controller methods
        mocker.patch.object(
            initialized_display._controller, "pack_pixels", return_value=b"\x00" * 1000
        )
        mock_load_start = mocker.patch.object(
            initialized_display._controller, "load_image_area_start"
        )
        mocker.patch.object(initialized_display._controller, "load_image_write")
        mocker.patch.object(initialized_display._controller, "load_image_end")
        mocker.patch.object(initialized_display._controller, "display_area")

        # Display with 1bpp and small chunk height (will be aligned to 32)
        initialized_display.display_image_progressive(
            img, pixel_format=PixelFormat.BPP_1, chunk_height=20
        )

        # Check that chunk height was aligned to 32 pixels
        # 100 pixels / 32 pixels per chunk = 4 chunks (rounded up)
        assert mock_load_start.call_count == 4

    def test_display_image_progressive_validation(self, initialized_display: EPaperDisplay) -> None:
        """Test progressive display validation."""
        # Image too wide
        img = Image.new("L", (2000, 100))
        with pytest.raises(InvalidParameterError, match="exceeds panel width"):
            initialized_display.display_image_progressive(img)

        # Image too tall
        img = Image.new("L", (100, 1000))
        with pytest.raises(InvalidParameterError, match="exceeds panel height"):
            initialized_display.display_image_progressive(img, y=100)


class TestA2ModeAutoClearing:
    """Test A2 mode auto-clear protection functionality."""

    @pytest.fixture
    def display_with_a2_limit(self, mocker: MockerFixture) -> EPaperDisplay:
        """Create display with A2 refresh limit."""
        mock_spi = MockSPI()
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi, a2_refresh_limit=5)

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
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi, a2_refresh_limit=10)

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
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi, a2_refresh_limit=0)

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

        # Several A2 refreshes should not trigger clear
        img = Image.new("L", (100, 100), color=128)
        # Test with 5 iterations instead of 20 - sufficient to verify behavior
        for _ in range(5):
            display.display_image(img, mode=DisplayMode.A2)
            assert display.a2_refresh_count == 0  # Counter stays at 0 when disabled

        # Clear should not have been called
        mock_clear.assert_called_once()  # Only during init

    def test_a2_warning_and_auto_clear_edge_case(self, mocker: MockerFixture) -> None:
        """Test A2 warning at limit-1 and auto-clear at limit with edge cases."""
        mock_spi = MockSPI()
        display = EPaperDisplay(
            vcom=-2.0, spi_interface=mock_spi, a2_refresh_limit=2
        )  # Very low limit

        # Mock initialization
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])  # VCOM

        # Mock _wait_display_ready and controller methods
        mocker.patch.object(display._controller, "_wait_display_ready")
        mocker.patch.object(display._controller, "pack_pixels", return_value=b"\x00" * 100)
        mocker.patch.object(display._controller, "load_image_area_start")
        mocker.patch.object(display._controller, "load_image_write")
        mocker.patch.object(display._controller, "load_image_end")
        mocker.patch.object(display._controller, "display_area")

        # Mock clear for init
        mock_clear = mocker.patch.object(display, "clear")

        display.init()
        mock_clear.reset_mock()

        img = Image.new("L", (100, 100), color=128)

        # First A2 refresh (count becomes 1, which equals limit-1, so warning triggers)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            display.display_image(img, mode=DisplayMode.A2)
            assert len(w) == 2  # Two warnings: pixel format and approaching limit
            # Check for both warnings
            warning_messages = [str(warn.message) for warn in w]
            assert any("works best with" in msg for msg in warning_messages)  # Pixel format warning
            assert any("approaching limit" in msg for msg in warning_messages)  # A2 limit warning
            assert display.a2_refresh_count == 1

        # Second A2 refresh (count becomes 2, should trigger auto-clear)
        display.display_image(img, mode=DisplayMode.A2)

        # Should have auto-cleared
        mock_clear.assert_called_once()
        assert display.a2_refresh_count == 0

    def test_properties(self) -> None:
        """Test A2 refresh properties."""
        display = EPaperDisplay(vcom=-2.0, a2_refresh_limit=7)

        assert display.a2_refresh_count == 0
        assert display.a2_refresh_limit == 7

        # Test with disabled auto-clear
        display2 = EPaperDisplay(vcom=-2.0, a2_refresh_limit=0)
        assert display2.a2_refresh_limit == 0


class TestPowerManagement:
    """Test power management features."""

    @pytest.fixture
    def display(self, mocker: MockerFixture) -> EPaperDisplay:
        """Create display with mocked components."""
        mock_spi = MockSPI()
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Mock initialization
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])  # VCOM

        mocker.patch.object(display, "clear")
        display.init()
        return display

    def test_power_state_property(self, display: EPaperDisplay, mocker: MockerFixture) -> None:
        """Test power_state property."""
        from IT8951_ePaper_Py.constants import PowerState

        # Mock the controller's _power_state attribute directly
        display._controller._power_state = PowerState.SLEEP
        assert display.power_state == PowerState.SLEEP

        # Change the mocked value
        display._controller._power_state = PowerState.STANDBY
        assert display.power_state == PowerState.STANDBY

    def test_wake_method(self, display: EPaperDisplay, mocker: MockerFixture) -> None:
        """Test wake method."""
        mock_wake = mocker.patch.object(display._controller, "wake")
        mock_update_time = mocker.patch.object(display, "_update_activity_time")

        display.wake()

        mock_wake.assert_called_once()
        mock_update_time.assert_called_once()

    def test_set_auto_sleep_timeout(self, display: EPaperDisplay, mocker: MockerFixture) -> None:
        """Test setting auto-sleep timeout."""
        mock_update_time = mocker.patch.object(display, "_update_activity_time")

        # Set valid timeout
        display.set_auto_sleep_timeout(30.0)
        assert display._auto_sleep_timeout == 30.0
        mock_update_time.assert_called_once()

        # Set None to disable
        display.set_auto_sleep_timeout(None)
        assert display._auto_sleep_timeout is None

        # Test invalid timeout
        with pytest.raises(InvalidParameterError, match="Auto-sleep timeout must be positive"):
            display.set_auto_sleep_timeout(0)

        with pytest.raises(InvalidParameterError, match="Auto-sleep timeout must be positive"):
            display.set_auto_sleep_timeout(-5.0)

    def test_check_auto_sleep(self, display: EPaperDisplay, mocker: MockerFixture) -> None:
        """Test auto-sleep checking."""
        from IT8951_ePaper_Py.constants import PowerState

        # Mock time
        mock_time = mocker.patch("time.time")
        mock_sleep = mocker.patch.object(display, "sleep")

        # Set up auto-sleep timeout
        mock_time.return_value = 100.0  # Initial time
        display.set_auto_sleep_timeout(10.0)  # 10 second timeout

        # Check immediately - should not sleep
        mock_time.return_value = 105.0  # 5 seconds later
        display.check_auto_sleep()
        mock_sleep.assert_not_called()

        # Check after timeout - should sleep
        mock_time.return_value = 111.0  # 11 seconds later
        # Mock the power_state to return ACTIVE
        display._controller._power_state = PowerState.ACTIVE
        display.check_auto_sleep()
        mock_sleep.assert_called_once()

        # Check when already in sleep mode - should not sleep again
        mock_sleep.reset_mock()
        # Mock the power_state to return SLEEP
        display._controller._power_state = PowerState.SLEEP
        display.check_auto_sleep()
        mock_sleep.assert_not_called()

        # Check when auto-sleep is disabled
        display.set_auto_sleep_timeout(None)
        mock_sleep.reset_mock()
        display.check_auto_sleep()
        mock_sleep.assert_not_called()

    def test_context_manager(self, mocker: MockerFixture) -> None:
        """Test context manager functionality."""
        mock_spi = MockSPI()

        # Set up read data for init
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])  # VCOM

        # Mock wait_display_ready to avoid timeout
        mocker.patch("IT8951_ePaper_Py.it8951.IT8951._wait_display_ready")

        # Create display and mock methods
        with EPaperDisplay(vcom=-2.0, spi_interface=mock_spi) as display:
            # Verify init was called
            assert display._initialized

            # Set auto-sleep timeout
            display.set_auto_sleep_timeout(5.0)

        # After context exit, display should be closed
        assert not display._initialized

    def test_context_manager_with_auto_sleep(self, mocker: MockerFixture) -> None:
        """Test context manager with auto-sleep on exit."""
        from IT8951_ePaper_Py.constants import PowerState

        mock_spi = MockSPI()

        # Set up read data for init
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])  # VCOM

        # Mock wait_display_ready to avoid timeout
        mocker.patch("IT8951_ePaper_Py.it8951.IT8951._wait_display_ready")

        # Track sleep calls
        mock_sleep = mocker.Mock()

        with EPaperDisplay(vcom=-2.0, spi_interface=mock_spi) as display:
            # Mock sleep method
            display.sleep = mock_sleep

            # Mock power state to return ACTIVE
            display._controller._power_state = PowerState.ACTIVE

            # Set auto-sleep timeout
            display.set_auto_sleep_timeout(10.0)

        # Sleep should have been called on exit
        mock_sleep.assert_called_once()


class TestMemoryAndEstimation:
    """Test memory estimation and edge cases."""

    def test_estimate_memory_usage_edge_cases(self) -> None:
        """Test _estimate_memory_usage with various pixel formats."""
        display = EPaperDisplay(vcom=-2.0)

        # Test BPP_8
        assert display._estimate_memory_usage(100, 100, PixelFormat.BPP_8) == 10000

        # Test BPP_4
        assert display._estimate_memory_usage(100, 100, PixelFormat.BPP_4) == 5000

        # Test BPP_2
        assert display._estimate_memory_usage(100, 100, PixelFormat.BPP_2) == 2500

        # Test BPP_1
        assert display._estimate_memory_usage(100, 100, PixelFormat.BPP_1) == 1250

        # Test default case - we'll create a mock pixel format value
        # that doesn't match any of the known formats
        invalid_format = 99  # Not a valid PixelFormat value
        # Since the method has a default case that returns pixels (worst case),
        # we can test it by passing an int directly
        assert display._estimate_memory_usage(100, 100, invalid_format) == 10000  # type: ignore

    def test_memory_limit_exceeded(self, mocker: MockerFixture) -> None:
        """Test handling when memory usage exceeds safe limit."""
        mock_spi = MockSPI()
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Mock initialization
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])  # VCOM

        mocker.patch.object(display, "clear")
        display.init()

        # Create an image that would exceed safe memory limit
        # Mock _estimate_memory_usage to return a value over the limit
        mocker.patch.object(
            display,
            "_estimate_memory_usage",
            return_value=MemoryConstants.SAFE_IMAGE_MEMORY_BYTES + 1,
        )

        img = Image.new("L", (100, 100))

        with pytest.raises(IT8951MemoryError, match="exceeds safe limit"):
            display.display_image(img)

    def test_progressive_display_chunk_alignment(self, mocker: MockerFixture) -> None:
        """Test chunk height alignment in progressive display."""
        mock_spi = MockSPI()
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Mock initialization
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])  # VCOM

        mocker.patch.object(display, "clear")
        display.init()

        # Mock controller methods
        mocker.patch.object(display._controller, "pack_pixels", return_value=b"\x00" * 1000)
        mocker.patch.object(display._controller, "load_image_area_start")
        mocker.patch.object(display._controller, "load_image_write")
        mocker.patch.object(display._controller, "load_image_end")
        mocker.patch.object(display._controller, "display_area")

        # Test with chunk_height = 0 for non-1bpp (should become 4)
        img = Image.new("L", (100, 100))
        display.display_image_progressive(img, chunk_height=3, pixel_format=PixelFormat.BPP_4)

        # Test with chunk_height = 0 for 1bpp (should become 32)
        display.display_image_progressive(img, chunk_height=1, pixel_format=PixelFormat.BPP_1)

    def test_progressive_display_zero_chunk_height(self, mocker: MockerFixture) -> None:
        """Test progressive display with chunk height that aligns to 0."""
        mock_spi = MockSPI()
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Mock initialization
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])  # VCOM

        mocker.patch.object(display, "clear")
        display.init()

        # Mock controller methods
        mocker.patch.object(display._controller, "pack_pixels", return_value=b"\x00" * 1000)
        mock_load_start = mocker.patch.object(display._controller, "load_image_area_start")
        mocker.patch.object(display._controller, "load_image_write")
        mocker.patch.object(display._controller, "load_image_end")
        mocker.patch.object(display._controller, "display_area")

        # Create small image
        img = Image.new("L", (64, 64))

        # Test with chunk_height that would align to 0 for non-1bpp
        # When chunk_height < 4 and aligns to 0, it should become 4
        display.display_image_progressive(img, chunk_height=1, pixel_format=PixelFormat.BPP_4)

        # For 1bpp, when chunk_height < 32 and aligns to 0, it should become 32
        mock_load_start.reset_mock()
        display.display_image_progressive(img, chunk_height=10, pixel_format=PixelFormat.BPP_1)


class TestCloseEdgeCases:
    """Test edge cases in close method."""

    def test_close_without_controller(self) -> None:
        """Test close when controller is None."""
        display = EPaperDisplay(vcom=-2.0)
        display._controller = None  # type: ignore

        # Should not raise an error
        display.close()
        assert not display._initialized

    def test_close_multiple_times(self, mocker: MockerFixture) -> None:
        """Test calling close multiple times."""
        mock_spi = MockSPI()
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Mock initialization
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])  # VCOM

        mocker.patch.object(display, "clear")
        display.init()

        mock_controller_close = mocker.patch.object(display._controller, "close")

        # First close
        display.close()
        assert not display._initialized
        mock_controller_close.assert_called_once()

        # Second close should still work
        mock_controller_close.reset_mock()
        display.close()
        # Controller close should be called again since controller still exists
        mock_controller_close.assert_called_once()
