"""Performance benchmarks for display modes."""

import time

import pytest
from PIL import Image

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode, PixelFormat
from IT8951_ePaper_Py.models import DeviceInfo


@pytest.fixture
def display(mocker):
    """Create display with mocked SPI for benchmarking."""
    # Mock SPI interface
    mock_spi = mocker.MagicMock()
    mocker.patch("IT8951_ePaper_Py.display.RaspberryPiSPI", return_value=mock_spi)

    # Create display
    display = EPaperDisplay(vcom=-2.0)

    # Mock device info
    device_info = DeviceInfo(
        panel_width=1872,
        panel_height=1404,
        memory_addr_l=0x0000,
        memory_addr_h=0x0010,
        fw_version="1.0.0",
        lut_version="M841",
    )
    mocker.patch.object(display._controller, "get_device_info", return_value=device_info)

    # Mock initialization
    mocker.patch.object(display._controller, "init")
    mocker.patch.object(display._controller, "set_vcom")

    # Initialize display
    display.init()

    # Mock the actual transfer methods to simulate realistic timing
    def mock_load_image(image_data, x, y, width, height) -> None:
        # Simulate transfer time based on data size
        data_size = len(image_data)
        # Assume 10MB/s transfer rate
        time.sleep(data_size / (10 * 1024 * 1024))

    def mock_display_area(x, y, width, height, mode) -> None:
        # Simulate display update time based on mode and area
        area_pixels = width * height
        total_pixels = 1872 * 1404
        area_ratio = area_pixels / total_pixels

        # Base timings for full screen (in seconds)
        mode_timings = {
            DisplayMode.INIT: 2.0,
            DisplayMode.DU: 0.26,
            DisplayMode.GC16: 0.45,
            DisplayMode.GL16: 0.45,
            DisplayMode.A2: 0.12,
            DisplayMode.DU4: 0.30,
            DisplayMode.GLR16: 0.50,
            DisplayMode.GLD16: 0.50,
        }

        base_time = mode_timings.get(mode, 0.5)
        time.sleep(base_time * area_ratio)

    # Mock the internal methods used by display_image
    mocker.patch.object(display._controller, "_load_image_to_memory", side_effect=mock_load_image)

    # Mock display_area to simulate timing
    def mock_display_area_wrapper(area, wait=True) -> None:
        mock_display_area(area.x, area.y, area.width, area.height, area.mode)

    mocker.patch.object(display._controller, "display_area", side_effect=mock_display_area_wrapper)

    return display


class TestDisplayModePerformance:
    """Benchmark tests for display mode performance."""

    def test_mode_switching_performance(self, display):
        """Test performance of switching between different display modes."""
        # Create test images
        sizes = [(100, 100), (500, 500), (1000, 1000), (1872, 1404)]
        test_images = {}
        for size in sizes:
            img = Image.new("L", size, 128)
            test_images[size] = img

        # Test all display modes
        modes = [
            DisplayMode.DU,
            DisplayMode.GC16,
            DisplayMode.GL16,
            DisplayMode.A2,
            DisplayMode.GLR16,
            DisplayMode.GLD16,
            DisplayMode.DU4,
        ]

        results = {}

        for size, img in test_images.items():
            results[size] = {}

            for mode in modes:
                # Measure display time
                start_time = time.time()
                display.display_image(img, mode=mode)
                elapsed = time.time() - start_time

                results[size][mode.name] = elapsed

        # Verify performance characteristics
        for size in sizes:
            size_results = results[size]

            # DU and A2 should be fastest
            assert size_results["DU"] < size_results["GC16"]
            assert size_results["A2"] < size_results["GC16"]

            # GC16/GL16 should be similar
            assert abs(size_results["GC16"] - size_results["GL16"]) < 0.1

            # Extended modes should be slower than basic modes
            if "GLR16" in size_results:
                assert size_results["GLR16"] >= size_results["GL16"]

    def test_pixel_format_impact_on_modes(self, display):
        """Test how different pixel formats affect mode performance."""
        # Create test image
        img = Image.new("L", (800, 600), 128)

        formats = [PixelFormat.BPP_1, PixelFormat.BPP_2, PixelFormat.BPP_4, PixelFormat.BPP_8]
        modes = [DisplayMode.DU, DisplayMode.GC16, DisplayMode.A2]

        results = {}

        for pixel_format in formats:
            results[pixel_format.name] = {}

            for mode in modes:
                # Measure time
                start_time = time.time()
                display.display_image(img, mode=mode, pixel_format=pixel_format)
                elapsed = time.time() - start_time

                results[pixel_format.name][mode.name] = elapsed

        # Verify lower bit depths are faster
        for mode in modes:
            mode_name = mode.name
            assert results["BPP_1"][mode_name] <= results["BPP_2"][mode_name]
            assert results["BPP_2"][mode_name] <= results["BPP_4"][mode_name]
            assert results["BPP_4"][mode_name] <= results["BPP_8"][mode_name]

    def test_partial_update_performance(self, display):
        """Benchmark partial update vs full screen update."""
        # Create test images
        full_img = Image.new("L", (1872, 1404), 128)
        partial_sizes = [(100, 100), (200, 200), (500, 500), (1000, 1000)]

        results = {"full_screen": {}}

        # Test full screen with different modes
        modes = [DisplayMode.DU, DisplayMode.GC16, DisplayMode.A2]

        for mode in modes:
            start_time = time.time()
            display.display_image(full_img, mode=mode)
            results["full_screen"][mode.name] = time.time() - start_time

        # Test partial updates
        for size in partial_sizes:
            partial_img = Image.new("L", size, 128)
            results[f"partial_{size[0]}x{size[1]}"] = {}

            for mode in modes:
                start_time = time.time()
                display.display_image(partial_img, x=0, y=0, mode=mode)
                elapsed = time.time() - start_time
                results[f"partial_{size[0]}x{size[1]}"][mode.name] = elapsed

        # Verify partial updates are faster
        for size in partial_sizes:
            key = f"partial_{size[0]}x{size[1]}"
            for mode in modes:
                assert results[key][mode.name] < results["full_screen"][mode.name]

    def test_mode_sequence_optimization(self, display):
        """Test performance of mode sequences (e.g., INIT followed by GC16)."""
        img = Image.new("L", (1872, 1404), 128)

        # Test single mode
        start_time = time.time()
        display.display_image(img, mode=DisplayMode.GC16)
        single_gc16_time = time.time() - start_time

        # Test INIT + GC16 sequence
        start_time = time.time()
        display.clear()  # Uses INIT mode
        display.display_image(img, mode=DisplayMode.GC16)
        init_gc16_time = time.time() - start_time

        # INIT + GC16 should take longer than just GC16
        assert init_gc16_time > single_gc16_time

        # Test rapid A2 updates
        a2_times = []
        for _i in range(5):
            start_time = time.time()
            display.display_image(img, mode=DisplayMode.A2)
            a2_times.append(time.time() - start_time)

        # A2 updates should be consistent
        avg_a2_time = sum(a2_times) / len(a2_times)
        for t in a2_times:
            assert abs(t - avg_a2_time) < 0.05  # Within 50ms

    @pytest.mark.parametrize(
        "mode",
        [
            DisplayMode.DU,
            DisplayMode.GC16,
            DisplayMode.GL16,
            DisplayMode.A2,
        ],
    )
    def test_mode_scaling_performance(self, display, mode):
        """Test how modes scale with image size."""
        sizes = [(100, 100), (500, 500), (1000, 1000), (1500, 1500)]
        times = []

        for size in sizes:
            img = Image.new("L", size, 128)
            start_time = time.time()
            display.display_image(img, mode=mode)
            times.append(time.time() - start_time)

        # Time should increase with area
        for i in range(1, len(sizes)):
            prev_area = sizes[i - 1][0] * sizes[i - 1][1]
            curr_area = sizes[i][0] * sizes[i][1]
            area_ratio = curr_area / prev_area
            time_ratio = times[i] / times[i - 1]

            # Time ratio should be roughly proportional to area ratio
            # Allow 50% deviation for overhead
            assert 0.5 * area_ratio <= time_ratio <= 1.5 * area_ratio

    def test_mode_memory_efficiency(self, display):
        """Test memory usage patterns for different modes."""
        # This test verifies that modes handle memory efficiently
        img = Image.new("L", (1872, 1404), 128)

        # Modes that should use less memory (1-bit internal processing)
        efficient_modes = [DisplayMode.DU, DisplayMode.A2]

        # Modes that need full grayscale
        full_modes = [DisplayMode.GC16, DisplayMode.GL16]

        # The actual memory usage is mocked, but we verify the calls
        for mode in efficient_modes:
            display.display_image(img, mode=mode, pixel_format=PixelFormat.BPP_1)
            # Should complete without memory errors

        for mode in full_modes:
            display.display_image(img, mode=mode, pixel_format=PixelFormat.BPP_8)
            # Should complete without memory errors
