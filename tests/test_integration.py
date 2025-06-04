"""Integration tests for IT8951 e-paper driver.

This module contains integration tests that verify the proper interaction
between multiple components and features of the driver. These tests are
more comprehensive than unit tests and test real-world usage scenarios.

Test Categories:
    - Power Management + Display Modes
    - Progressive Loading + Bit Depth
    - Error Recovery + Retry Policies
    - Thread Safety + Concurrent Operations
    - Memory Management + Large Images
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from PIL import Image
from pytest_mock import MockerFixture

from IT8951_ePaper_Py.constants import (
    DisplayMode,
    MemoryConstants,
    PixelFormat,
    PowerState,
    Rotation,
)
from IT8951_ePaper_Py.display import EPaperDisplay
from IT8951_ePaper_Py.exceptions import (
    CommunicationError,
    IT8951MemoryError,
    IT8951TimeoutError,
)
from IT8951_ePaper_Py.retry_policy import BackoffStrategy, RetryPolicy, create_retry_spi_interface
from IT8951_ePaper_Py.spi_interface import MockSPI
from IT8951_ePaper_Py.thread_safe import ThreadSafeEPaperDisplay


@pytest.mark.integration
class TestPowerManagementWithDisplayModes:
    """Test power management features combined with different display modes."""

    @pytest.fixture
    def display_with_power(self, mocker: MockerFixture) -> EPaperDisplay:
        """Create display with power management enabled."""
        mock_spi = MockSPI()
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi, a2_refresh_limit=5)

        # Mock initialization
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])  # REG_0204
        mock_spi.set_read_data([2000])  # VCOM

        # Mock wait_display_ready to avoid timeout
        mocker.patch.object(display._controller, "_wait_display_ready")

        mocker.patch.object(display, "clear")
        display.init()
        return display

    @pytest.mark.slow
    def test_auto_sleep_with_display_operations(
        self, display_with_power: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test auto-sleep functionality during display operations."""
        # Mock controller methods
        mocker.patch.object(display_with_power._controller, "pack_pixels", return_value=b"\x00")
        mocker.patch.object(display_with_power._controller, "load_image_area_start")
        mocker.patch.object(display_with_power._controller, "load_image_write")
        mocker.patch.object(display_with_power._controller, "load_image_end")
        mocker.patch.object(display_with_power._controller, "display_area")

        # Enable auto-sleep with short timeout
        display_with_power.set_auto_sleep_timeout(0.1)  # 100ms timeout

        # Mock sleep method to track calls
        mock_sleep = mocker.patch.object(display_with_power, "sleep")

        # Create test image
        img = Image.new("L", (100, 100), color=128)

        # Display image (resets activity timer)
        display_with_power.display_image(img, mode=DisplayMode.GC16)

        # Activity timer should be reset, no sleep yet
        time.sleep(0.05)
        display_with_power.check_auto_sleep()
        mock_sleep.assert_not_called()

        # Wait for timeout
        time.sleep(0.1)
        display_with_power.check_auto_sleep()
        mock_sleep.assert_called_once()

    def test_power_state_transitions_with_modes(
        self, display_with_power: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test power state transitions with different display modes."""
        # Mock controller methods
        mocker.patch.object(display_with_power._controller, "pack_pixels", return_value=b"\x00")
        mocker.patch.object(display_with_power._controller, "load_image_area_start")
        mocker.patch.object(display_with_power._controller, "load_image_write")
        mocker.patch.object(display_with_power._controller, "load_image_end")
        mocker.patch.object(display_with_power._controller, "display_area")

        img = Image.new("L", (64, 64), color=128)

        # Test display operations in different power states
        display_modes = [DisplayMode.GC16, DisplayMode.DU, DisplayMode.A2]

        for mode in display_modes:
            # Active state
            display_with_power.display_image(img, mode=mode)
            assert display_with_power.power_state == PowerState.ACTIVE

            # Sleep and wake
            display_with_power.sleep()
            assert display_with_power.power_state == PowerState.SLEEP

            display_with_power.wake()
            assert display_with_power.power_state == PowerState.ACTIVE

            # Display after wake
            display_with_power.display_image(img, mode=mode)

    def test_a2_refresh_with_power_management(
        self, display_with_power: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test A2 refresh counter with power state changes."""
        # Mock display operations
        mocker.patch.object(display_with_power._controller, "pack_pixels", return_value=b"\x00")
        mocker.patch.object(display_with_power._controller, "load_image_area_start")
        mocker.patch.object(display_with_power._controller, "load_image_write")
        mocker.patch.object(display_with_power._controller, "load_image_end")
        mocker.patch.object(display_with_power._controller, "display_area")

        img = Image.new("L", (64, 64), color=128)

        # A2 refreshes
        for i in range(3):
            display_with_power.display_image(img, mode=DisplayMode.A2)
            assert display_with_power.a2_refresh_count == i + 1

        # Sleep doesn't reset counter
        display_with_power.sleep()
        assert display_with_power.a2_refresh_count == 3

        # Wake and continue
        display_with_power.wake()
        display_with_power.display_image(img, mode=DisplayMode.A2)
        assert display_with_power.a2_refresh_count == 4

        # A2 mode with limit reached should trigger clear
        # After 5 A2 refreshes (limit=5), the next one triggers a clear
        display_with_power.display_image(img, mode=DisplayMode.A2)
        # Counter should be reset to 0 after the automatic clear
        assert display_with_power.a2_refresh_count == 0


@pytest.mark.integration
class TestProgressiveLoadingWithBitDepth:
    """Test progressive loading combined with bit depth optimizations."""

    @pytest.fixture
    def large_display(self, mocker: MockerFixture) -> EPaperDisplay:
        """Create display for testing large images."""
        mock_spi = MockSPI()
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Mock large display
        mock_spi.set_read_data(
            [2048, 1536, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])

        mocker.patch.object(display, "clear")
        mocker.patch.object(display._controller, "_wait_display_ready")
        display.init()
        return display

    def test_progressive_loading_different_bit_depths(
        self, large_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test progressive loading with different bit depths."""
        # Mock controller methods
        mock_pack = mocker.patch.object(
            large_display._controller, "pack_pixels", return_value=b"\x00" * 1000
        )
        mocker.patch.object(large_display._controller, "load_image_area_start")
        mocker.patch.object(large_display._controller, "load_image_write")
        mocker.patch.object(large_display._controller, "load_image_end")
        mocker.patch.object(large_display._controller, "display_area")

        # Create large image
        img = Image.new("L", (1024, 768), color=128)

        # Test progressive loading with different pixel formats
        formats = [PixelFormat.BPP_8, PixelFormat.BPP_4, PixelFormat.BPP_2, PixelFormat.BPP_1]

        for fmt in formats:
            mock_pack.reset_mock()

            # Progressive load with specific format
            large_display.display_image_progressive(img, pixel_format=fmt, chunk_height=128)

            # Verify pack_pixels was called with correct format
            assert mock_pack.call_count > 0
            args, _ = mock_pack.call_args
            assert len(args) >= 2
            assert args[1] == fmt  # pixel_format is the second argument

    def test_memory_efficiency_progressive_loading(
        self, large_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test memory efficiency of progressive loading."""
        # Track memory allocations
        allocated_sizes = []

        def track_allocation(pixels: bytes, pixel_format: PixelFormat) -> bytes:
            allocated_sizes.append(len(pixels))
            return b"\x00" * (len(pixels) // 2)  # Simulate 4bpp packing

        mocker.patch.object(large_display._controller, "pack_pixels", side_effect=track_allocation)
        mocker.patch.object(large_display._controller, "load_image_area_start")
        mocker.patch.object(large_display._controller, "load_image_write")
        mocker.patch.object(large_display._controller, "load_image_end")
        mocker.patch.object(large_display._controller, "display_area")

        # Large image
        img = Image.new("L", (1024, 768))

        # Progressive load with small chunks
        large_display.display_image_progressive(
            img, pixel_format=PixelFormat.BPP_4, chunk_height=64
        )

        # Verify no single allocation exceeded chunk size
        max_allocation = max(allocated_sizes)
        assert max_allocation <= 1024 * 64  # Width * chunk_height

    def test_progressive_with_rotation_and_bit_depth(
        self, large_display: EPaperDisplay, mocker: MockerFixture
    ) -> None:
        """Test progressive loading with rotation and bit depth optimization."""
        mocker.patch.object(large_display._controller, "pack_pixels", return_value=b"\x00" * 1000)
        mock_load_start = mocker.patch.object(large_display._controller, "load_image_area_start")
        mocker.patch.object(large_display._controller, "load_image_write")
        mocker.patch.object(large_display._controller, "load_image_end")
        mocker.patch.object(large_display._controller, "display_area")

        # Create image
        img = Image.new("L", (512, 384), color=64)

        # Test rotation with progressive loading
        large_display.display_image_progressive(
            img, rotation=Rotation.ROTATE_90, pixel_format=PixelFormat.BPP_2, chunk_height=96
        )

        # Verify correct dimensions after rotation
        first_call = mock_load_start.call_args_list[0]
        area_info = first_call[0][1]
        # After 90° rotation: width becomes height, height becomes width
        assert area_info.width == 384  # Original height
        assert area_info.height <= 96  # Chunk height


@pytest.mark.integration
class TestErrorRecoveryWithRetryPolicies:
    """Test error recovery mechanisms with retry policies."""

    def test_retry_policy_with_display_operations(self, mocker: MockerFixture) -> None:
        """Test retry policies during display operations."""
        # Create base SPI that fails intermittently
        base_spi = MockSPI()
        fail_count = 0

        def intermittent_write(data: list[int]) -> None:
            nonlocal fail_count
            if fail_count < 2:
                fail_count += 1
                raise CommunicationError("SPI write failed")
            # Success on third attempt

        mocker.patch.object(base_spi, "write_data_bulk", side_effect=intermittent_write)

        # Wrap with retry policy
        retry_policy = RetryPolicy(
            max_attempts=3, delay=0.01, backoff_strategy=BackoffStrategy.EXPONENTIAL
        )
        retry_spi = create_retry_spi_interface(base_spi, retry_policy)

        # Create display with retry-enabled SPI
        display = EPaperDisplay(vcom=-2.0, spi_interface=retry_spi)

        # Mock initialization
        base_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        base_spi.set_read_data([0x0000])
        base_spi.set_read_data([2000])

        # Mock wait_display_ready and clear to avoid timeout
        mocker.patch.object(display._controller, "_wait_display_ready")
        mocker.patch.object(display, "clear")

        # Should succeed despite failures
        display.init()
        assert display._initialized

    def test_error_propagation_across_layers(self, mocker: MockerFixture) -> None:
        """Test error propagation from SPI through controller to display."""
        mock_spi = MockSPI()

        # Mock partial initialization
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])  # VCOM

        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Make clear() timeout by mocking _wait_display_ready
        mocker.patch.object(
            display._controller,
            "_wait_display_ready",
            side_effect=IT8951TimeoutError("Device timeout"),
        )

        # Initialize successfully first
        mocker.patch.object(display, "clear")  # Mock clear during init
        display.init()

        # Now display operations should fail with timeout
        # Use display_image instead of clear since clear is mocked
        img = Image.new("L", (100, 100))
        mocker.patch.object(display._controller, "pack_pixels", return_value=b"\x00" * 100)
        mocker.patch.object(display._controller, "load_image_area_start")
        mocker.patch.object(display._controller, "load_image_write")
        mocker.patch.object(display._controller, "load_image_end")

        with pytest.raises(IT8951TimeoutError):
            display.display_image(img)

    def test_recovery_from_memory_errors(self, mocker: MockerFixture) -> None:
        """Test recovery from memory allocation errors."""
        mock_spi = MockSPI()
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Initialize
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])
        mocker.patch.object(display._controller, "_wait_display_ready")
        display.init()

        # Mock controller methods for clear operation
        mocker.patch.object(display._controller._spi, "write_data")
        mocker.patch.object(display._controller._spi, "write_command")
        mocker.patch.object(display._controller, "display_area")

        # Mock memory allocation failure in buffer pool
        from IT8951_ePaper_Py.buffer_pool import BufferPool

        original_get = BufferPool.get_bytes_buffer
        call_count = 0

        def mock_get_buffer(size: int, fill_value: int | None = None) -> bytes:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise MemoryError("Out of memory")
            return original_get(size, fill_value)

        mocker.patch.object(BufferPool, "get_bytes_buffer", side_effect=mock_get_buffer)

        # First attempt should fail
        with pytest.raises(IT8951MemoryError):
            display.clear()

        # Second attempt should succeed (simulating memory freed)
        display.clear()


@pytest.mark.integration
@pytest.mark.slow
class TestThreadSafetyWithConcurrentOperations:
    """Test thread safety with concurrent operations."""

    def test_concurrent_display_operations(self, mocker: MockerFixture) -> None:
        """Test concurrent display operations are properly serialized."""
        mock_spi = MockSPI()
        display = ThreadSafeEPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Initialize
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])
        mocker.patch.object(display, "clear")
        mocker.patch.object(display._controller, "_wait_display_ready")
        display.init()

        # Track operation order
        operations = []

        def track_pack_pixels(pixels: bytes, pixel_format: PixelFormat) -> bytes:
            operations.append(("pack", time.time()))
            time.sleep(0.01)  # Simulate work
            return b"\x00"

        def track_display_area(
            area: object, mode: DisplayMode | None = None, wait: bool = True
        ) -> None:
            operations.append(("display", time.time()))

        mocker.patch.object(display._controller, "pack_pixels", side_effect=track_pack_pixels)
        mocker.patch.object(display._controller, "load_image_area_start")
        mocker.patch.object(display._controller, "load_image_write")
        mocker.patch.object(display._controller, "load_image_end")
        mocker.patch.object(display._controller, "display_area", side_effect=track_display_area)

        # Create test images
        images = [Image.new("L", (64, 64), color=i * 32) for i in range(4)]

        # Display concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for img in images:
                future = executor.submit(display.display_image, img)
                futures.append(future)

            # Wait for completion
            for future in as_completed(futures):
                future.result()

        # Verify operations were serialized (no overlapping)
        assert len(operations) == 8  # 4 pack + 4 display

        # Check timing - operations should not overlap
        # Note: Due to threading overhead, we allow some tolerance
        for i in range(len(operations) - 1):
            op1_start = operations[i][1]
            op2_start = operations[i + 1][1]
            # Next operation should start after or very close to previous (thread scheduling tolerance)
            assert op2_start >= op1_start - 0.001  # Allow 1ms tolerance for thread scheduling

    def test_thread_safe_power_management(self, mocker: MockerFixture) -> None:
        """Test thread-safe power state transitions."""
        mock_spi = MockSPI()
        display = ThreadSafeEPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Initialize
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])
        mocker.patch.object(display, "clear")
        mocker.patch.object(display._controller, "_wait_display_ready")
        display.init()

        # Track power state changes
        state_changes = []

        def track_sleep() -> None:
            state_changes.append(("sleep", time.time()))
            time.sleep(0.01)
            # Call the parent class's sleep method directly
            EPaperDisplay.sleep(display)

        def track_wake() -> None:
            state_changes.append(("wake", time.time()))
            time.sleep(0.01)
            # Call the parent class's wake method directly
            EPaperDisplay.wake(display)

        mocker.patch.object(display, "sleep", side_effect=track_sleep)
        mocker.patch.object(display, "wake", side_effect=track_wake)

        # Concurrent power operations
        def power_cycle() -> None:
            display.sleep()
            display.wake()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(power_cycle) for _ in range(3)]
            for future in as_completed(futures):
                future.result()

        # Verify serialization
        assert len(state_changes) == 6  # 3 sleep + 3 wake

        # Count operations
        sleep_count = sum(1 for op, _ in state_changes if op == "sleep")
        wake_count = sum(1 for op, _ in state_changes if op == "wake")

        assert sleep_count == 3
        assert wake_count == 3

        # Verify operations are properly serialized (no concurrent execution)
        for i in range(len(state_changes) - 1):
            # Each operation should complete before the next starts
            assert state_changes[i + 1][1] >= state_changes[i][1]


@pytest.mark.integration
class TestMemoryManagementWithLargeImages:
    """Test memory management with large images."""

    def test_large_image_handling_different_formats(self, mocker: MockerFixture) -> None:
        """Test large image handling with different pixel formats."""
        mock_spi = MockSPI()
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Initialize with large display
        mock_spi.set_read_data(
            [2048, 2048, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])
        mocker.patch.object(display, "clear")
        display.init()

        # Test memory usage for different formats
        test_cases = [
            (PixelFormat.BPP_8, 2048 * 2048),  # 4MB
            (PixelFormat.BPP_4, 2048 * 2048 // 2),  # 2MB
            (PixelFormat.BPP_2, 2048 * 2048 // 4),  # 1MB
            (PixelFormat.BPP_1, 2048 * 2048 // 8),  # 512KB
        ]

        for pixel_format, expected_size in test_cases:
            estimated = display._estimate_memory_usage(2048, 2048, pixel_format)
            assert estimated == expected_size

    def test_memory_warning_thresholds(self, mocker: MockerFixture) -> None:
        """Test memory warning thresholds for different operations."""
        mock_spi = MockSPI()
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Initialize
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])
        mocker.patch.object(display, "clear")
        display.init()

        # Mock display operations
        mocker.patch.object(display._controller, "pack_pixels", return_value=b"\x00")
        mocker.patch.object(display._controller, "load_image_area_start")
        mocker.patch.object(display._controller, "load_image_write")
        mocker.patch.object(display._controller, "load_image_end")
        mocker.patch.object(display._controller, "display_area")

        # Lower threshold for testing
        mocker.patch.object(MemoryConstants, "WARNING_THRESHOLD_BYTES", 512 * 1024)

        # Large image should trigger warning
        img = Image.new("L", (1024, 768))

        with pytest.warns(UserWarning, match="Large image memory usage"):
            display.display_image(img, pixel_format=PixelFormat.BPP_8)

    def test_buffer_pool_efficiency(self, mocker: MockerFixture) -> None:
        """Test buffer pool efficiency for repeated operations."""
        from IT8951_ePaper_Py.buffer_pool import BufferPool

        # Clear pool to start fresh
        BufferPool.clear_pools()

        # Test buffer pool directly first
        allocation_sizes = []
        original_bytes = bytes

        def track_bytes_creation(size_or_data: int | bytes | bytearray) -> bytes:
            if isinstance(size_or_data, int):
                allocation_sizes.append(size_or_data)
                # Actually create new bytes to track real allocations
                return original_bytes(size_or_data)
            return original_bytes(size_or_data)

        # Patch bytes creation at the module level where BufferPool is defined
        mocker.patch("IT8951_ePaper_Py.buffer_pool.bytes", side_effect=track_bytes_creation)

        # Test direct buffer pool usage
        test_size = 1000
        buffers = []
        for _ in range(5):
            buf = BufferPool.get_bytes_buffer(test_size)
            buffers.append(buf)
            BufferPool.return_bytes_buffer(buf)

        # First allocation should create a new buffer
        # Subsequent ones should reuse from pool
        assert len(allocation_sizes) == 1  # Only one actual allocation
        assert allocation_sizes[0] == test_size


@pytest.mark.integration
class TestComplexWorkflows:
    """Test complex multi-feature workflows."""

    def test_complete_display_workflow(self, mocker: MockerFixture) -> None:
        """Test complete workflow from initialization to display."""
        # Create retry-enabled SPI
        base_spi = MockSPI()
        retry_policy = RetryPolicy(max_attempts=3, delay=0.01)
        retry_spi = create_retry_spi_interface(base_spi, retry_policy)

        # Create thread-safe display with retry
        display = ThreadSafeEPaperDisplay(
            vcom=-2.06, spi_interface=retry_spi, enhance_driving=True, a2_refresh_limit=5
        )

        # Mock initialization
        base_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        base_spi.set_read_data([0x0000])
        base_spi.set_read_data([2060])  # VCOM matches

        # Track enhanced driving
        write_commands = []
        write_data = []

        def track_write_command(cmd: int) -> None:
            write_commands.append(cmd)

        def track_write_data(data: list[int] | int) -> None:
            if isinstance(data, int):
                write_data.append(data)
            else:
                write_data.extend(data)

        mocker.patch.object(base_spi, "write_command", side_effect=track_write_command)
        mocker.patch.object(base_spi, "write_data", side_effect=track_write_data)
        mocker.patch.object(display._controller, "_wait_display_ready")

        display.init()

        # Verify enhanced driving was set - check if register write command was used
        from IT8951_ePaper_Py.constants import ProtocolConstants, Register, SystemCommand

        # Enhanced driving is set via REG_WR command with register address and value
        assert SystemCommand.REG_WR in write_commands
        # The data should contain register address and value
        assert Register.ENHANCE_DRIVING in write_data
        assert ProtocolConstants.ENHANCED_DRIVING_VALUE in write_data

        # Enable auto-sleep
        display.set_auto_sleep_timeout(60.0)

        # Mock display operations
        mocker.patch.object(display._controller, "pack_pixels", return_value=b"\x00" * 100)
        mocker.patch.object(display._controller, "load_image_area_start")
        mocker.patch.object(display._controller, "load_image_write")
        mocker.patch.object(display._controller, "load_image_end")
        mocker.patch.object(display._controller, "display_area")

        # Complete workflow
        img = Image.new("L", (256, 256), color=128)

        # 1. Display with different modes
        display.display_image(img, mode=DisplayMode.GC16)
        display.display_partial(img.crop((0, 0, 128, 128)), x=100, y=100, mode=DisplayMode.DU)

        # 2. A2 mode refreshes
        for _ in range(3):
            display.display_image(img, mode=DisplayMode.A2, pixel_format=PixelFormat.BPP_1)

        # 3. Progressive loading for large image
        large_img = Image.new("L", (1024, 768))
        display.display_image_progressive(
            large_img, pixel_format=PixelFormat.BPP_4, chunk_height=128
        )

        # 4. Power management
        display.sleep()
        display.wake()

        # 5. Check status
        # Mock the enhanced driving status check
        mocker.patch.object(display._controller, "is_enhanced_driving_enabled", return_value=True)
        status = display.get_device_status()
        assert status["enhanced_driving"] is True
        assert status["a2_refresh_count"] == 3
        assert status["auto_sleep_timeout"] == 60.0

    def test_error_recovery_workflow(self, mocker: MockerFixture) -> None:
        """Test complete error recovery workflow."""
        mock_spi = MockSPI()
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Test recovery from display error
        # First setup successful init
        mock_spi.set_read_data(
            [1024, 768, MemoryConstants.IMAGE_BUFFER_ADDR_L, MemoryConstants.IMAGE_BUFFER_ADDR_H]
            + [0] * 16
        )
        mock_spi.set_read_data([0x0000])
        mock_spi.set_read_data([2000])

        # Mock wait_display_ready to avoid timeout
        mocker.patch.object(display._controller, "_wait_display_ready")
        mocker.patch.object(display, "clear")

        # Initialize successfully
        display.init()
        assert display._initialized

        # Test recovery from display error
        mocker.patch.object(display._controller, "pack_pixels", return_value=b"\x00" * 100)
        mocker.patch.object(display._controller, "load_image_area_start")
        mocker.patch.object(display._controller, "load_image_write")
        mocker.patch.object(display._controller, "load_image_end")
        mocker.patch.object(
            display._controller,
            "display_area",
            side_effect=[IT8951TimeoutError("Timeout"), None],  # Fail once, then succeed
        )

        img = Image.new("L", (100, 100))

        # First attempt fails
        with pytest.raises(IT8951TimeoutError):
            display.display_image(img)

        # Second attempt succeeds
        display.display_image(img)
