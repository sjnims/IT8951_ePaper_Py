"""Performance benchmarks for display modes."""

import time

import pytest
from PIL import Image
from pytest_mock import MockerFixture

from IT8951_ePaper_Py.constants import DisplayMode, MemoryConstants, PixelFormat
from IT8951_ePaper_Py.display import EPaperDisplay
from IT8951_ePaper_Py.models import DisplayArea
from IT8951_ePaper_Py.spi_interface import MockSPI


class TestDisplayModePerformance:
    """Benchmark tests for different display modes."""

    @pytest.fixture
    def mock_spi(self) -> MockSPI:
        """Create mock SPI interface."""
        return MockSPI()

    @pytest.fixture
    def display(self, mock_spi: MockSPI, mocker: MockerFixture) -> EPaperDisplay:
        """Create and initialize EPaperDisplay for benchmarking."""
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)

        # Data for _get_device_info (20 values)
        mock_spi.set_read_data(
            [
                1872,  # panel_width
                1404,  # panel_height
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
                77,
                56,
                52,
                49,
                0,
                0,
                0,
                0,  # lut_version "M841"
            ]
        )
        # Data for _enable_packed_write register read
        mock_spi.set_read_data([0x0000])

        # Data for get_vcom() call in init() - return 2000 (2.0V)
        mock_spi.set_read_data([2000])

        # Mock clear to avoid complex setup
        mocker.patch.object(display, "clear")

        display.init()

        # Mock the actual display operations with timing simulation
        def mock_display_image(image, x=0, y=0, mode=DisplayMode.GC16) -> None:
            # Simulate display time based on mode
            if mode == DisplayMode.A2:
                time.sleep(0.001)  # Fastest
            elif mode == DisplayMode.DU:
                time.sleep(0.002)  # Fast
            elif mode == DisplayMode.GL16:
                time.sleep(0.005)  # Medium
            elif mode == DisplayMode.GC16:
                time.sleep(0.010)  # Slowest

        mocker.patch.object(display, "display_image", side_effect=mock_display_image)

        return display

    def test_display_mode_timing_comparison(self, display: EPaperDisplay):
        """Compare timing of different display modes."""
        # Create test images
        test_sizes = [(200, 200), (400, 400), (800, 600)]

        results = {}

        for width, height in test_sizes:
            img = Image.new("L", (width, height), 128)
            mode_times = {}

            # Test each display mode
            for mode in [DisplayMode.A2, DisplayMode.DU, DisplayMode.GL16, DisplayMode.GC16]:
                start = time.time()
                display.display_image(img, 0, 0, mode)
                elapsed = time.time() - start
                mode_times[mode.name] = elapsed

            results[f"{width}x{height}"] = mode_times

        # Print results
        for size, times in results.items():
            print(f"\n{size}:")
            for mode, time_taken in sorted(times.items(), key=lambda x: x[1]):
                print(f"  {mode}: {time_taken:.4f}s")

    def test_partial_update_mode_performance(self, display: EPaperDisplay):
        """Test performance of partial updates with different modes."""
        # Create small test areas
        test_areas = [
            DisplayArea(x=100, y=100, width=100, height=100),
            DisplayArea(x=300, y=300, width=200, height=200),
            DisplayArea(x=600, y=600, width=300, height=300),
        ]

        # Mock display_partial with timing
        def mock_display_partial(image, x, y, mode=DisplayMode.DU) -> None:
            if mode == DisplayMode.A2:
                time.sleep(0.0005)
            elif mode == DisplayMode.DU:
                time.sleep(0.001)
            else:
                time.sleep(0.003)

        display.display_partial = mock_display_partial

        results = {}

        for area in test_areas:
            img = Image.new("L", (area.width, area.height), 128)
            mode_times = {}

            # Test A2 and DU modes (recommended for partial updates)
            for mode in [DisplayMode.A2, DisplayMode.DU]:
                start = time.time()
                display.display_partial(img, area.x, area.y, mode)
                elapsed = time.time() - start
                mode_times[mode.name] = elapsed

            results[f"{area.width}x{area.height}"] = mode_times

        # Verify A2 is faster than DU
        for _size, times in results.items():
            assert times["A2"] < times["DU"]

    def test_mode_quality_vs_speed_tradeoff(self, display: EPaperDisplay):
        """Test the quality vs speed tradeoff of display modes."""
        # Create test patterns that show quality differences
        width, height = 400, 400

        # Gradient pattern (shows banding in low-quality modes)
        gradient = Image.new("L", (width, height))
        pixels = gradient.load()
        if pixels is not None:
            for y in range(height):
                for x in range(width):
                    pixels[x, y] = (x * 255) // width

        # Checkerboard pattern (shows ghosting)
        checkerboard = Image.new("L", (width, height))
        pixels = checkerboard.load()
        if pixels is not None:
            for y in range(height):
                for x in range(width):
                    pixels[x, y] = 255 if (x // 10 + y // 10) % 2 == 0 else 0

        # Text-like pattern (fine details)
        text_pattern = Image.new("L", (width, height), 255)
        pixels = text_pattern.load()
        # Create horizontal lines to simulate text
        if pixels is not None:
            for y in range(0, height, 20):
                for x in range(width):
                    if y % 40 < 3:
                        pixels[x, y] = 0

        patterns = {
            "gradient": gradient,
            "checkerboard": checkerboard,
            "text": text_pattern,
        }

        # Test each pattern with each mode
        results = {}
        for pattern_name, pattern in patterns.items():
            mode_times = {}

            for mode in [DisplayMode.A2, DisplayMode.DU, DisplayMode.GL16, DisplayMode.GC16]:
                start = time.time()
                display.display_image(pattern, 0, 0, mode)
                elapsed = time.time() - start
                mode_times[mode.name] = elapsed

            results[pattern_name] = mode_times

        # Print recommendations
        print("\nMode recommendations by content type:")
        print("- Text/UI: A2 (fastest, good for black/white)")
        print("- General content: DU (fast, decent quality)")
        print("- Photos: GL16/GC16 (slower, best quality)")

    def test_rapid_update_performance(self, display: EPaperDisplay):
        """Test performance of rapid sequential updates."""
        # Small area for rapid updates
        area = DisplayArea(x=100, y=100, width=100, height=100)
        img = Image.new("L", (area.width, area.height))

        # Test rapid updates with different modes
        update_counts = {
            DisplayMode.A2: 0,
            DisplayMode.DU: 0,
        }

        test_duration = 0.1  # 100ms test window

        for mode in [DisplayMode.A2, DisplayMode.DU]:
            start = time.time()
            count = 0

            while time.time() - start < test_duration:
                # Alternate between black and white
                img.putpixel((50, 50), 255 if count % 2 == 0 else 0)
                display.display_partial(img, area.x, area.y, mode)
                count += 1

            update_counts[mode] = count

        # A2 should achieve more updates
        assert update_counts[DisplayMode.A2] > update_counts[DisplayMode.DU]

        print(f"\nRapid update test ({test_duration}s):")
        for mode, count in update_counts.items():
            print(f"  {mode.name}: {count} updates ({count / test_duration:.1f} Hz)")

    def test_mode_switching_overhead(self, display: EPaperDisplay):
        """Test overhead of switching between display modes."""
        img = Image.new("L", (200, 200), 128)

        # Test same mode repeated updates
        same_mode_start = time.time()
        for _ in range(10):
            display.display_image(img, 0, 0, DisplayMode.DU)
        same_mode_time = time.time() - same_mode_start

        # Test alternating modes
        alternating_start = time.time()
        for i in range(10):
            mode = DisplayMode.DU if i % 2 == 0 else DisplayMode.A2
            display.display_image(img, 0, 0, mode)
        alternating_time = time.time() - alternating_start

        # Mode switching might add slight overhead
        overhead = alternating_time - same_mode_time
        print(f"\nMode switching overhead: {overhead:.4f}s ({overhead / 10:.4f}s per switch)")

    def test_pixel_format_impact_on_modes(self, display: EPaperDisplay):
        """Test how pixel format affects mode performance."""
        width, height = 400, 400

        # Test different pixel formats
        results = {}

        for pixel_format in [PixelFormat.BPP_1, PixelFormat.BPP_2, PixelFormat.BPP_4]:
            # Create appropriate image
            if pixel_format == PixelFormat.BPP_1:
                img = Image.new("1", (width, height), 1)
            else:
                img = Image.new("L", (width, height), 128)

            format_times = {}

            # Test with A2 and DU modes
            for mode in [DisplayMode.A2, DisplayMode.DU]:
                # Simulate that lower bit depth transfers faster
                transfer_factor = {
                    PixelFormat.BPP_1: 0.25,
                    PixelFormat.BPP_2: 0.5,
                    PixelFormat.BPP_4: 1.0,
                }[pixel_format]

                start = time.time()
                # Simulate transfer time
                time.sleep(0.001 * transfer_factor)
                display.display_image(img, 0, 0, mode)
                elapsed = time.time() - start

                format_times[mode.name] = elapsed

            results[pixel_format.name] = format_times

        # Print results
        print("\nPixel format impact on display modes:")
        for fmt, times in results.items():
            print(f"{fmt}:")
            for mode, time_taken in times.items():
                print(f"  {mode}: {time_taken:.4f}s")
