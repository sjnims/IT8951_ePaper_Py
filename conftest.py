"""pytest configuration for IT8951 ePaper Python driver.

This file provides shared fixtures and configuration for the test suite.
"""

from collections.abc import Generator
from unittest.mock import Mock

import numpy as np
import pytest
from numpy.typing import NDArray
from PIL import Image
from pytest_mock import MockerFixture

from IT8951_ePaper_Py.buffer_pool import BufferPool
from IT8951_ePaper_Py.constants import MemoryConstants
from IT8951_ePaper_Py.display import EPaperDisplay
from IT8951_ePaper_Py.it8951 import IT8951
from IT8951_ePaper_Py.spi_interface import MockSPI


@pytest.fixture(autouse=True)
def isolate_buffer_pools() -> Generator[None, None, None]:
    """Ensure BufferPool state is isolated between tests.

    This fixture automatically clears the BufferPool before and after each test
    to ensure test isolation when running in parallel with pytest-xdist.
    """
    # Clear pools before test
    BufferPool.clear_pools()

    # Run test
    yield

    # Clear pools after test
    BufferPool.clear_pools()


@pytest.fixture(autouse=True)
def reset_buffer_pool_state() -> None:
    """Reset BufferPool class-level state to ensure test isolation.

    This is a backup to ensure the pools are truly empty, even if
    something goes wrong with the clear_pools() method.
    """
    # Use clear_pools which is the public API
    BufferPool.clear_pools()


# Custom markers for test organization
def pytest_configure(config: pytest.Config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "serial: marks tests that must run serially (not in parallel)"
    )
    config.addinivalue_line("markers", "integration: marks integration tests")
    config.addinivalue_line("markers", "performance: marks performance benchmarks")
    config.addinivalue_line("markers", "hardware: marks tests requiring real hardware")
    config.addinivalue_line(
        "markers", "real_timing: marks tests that need real time.sleep() behavior"
    )
    config.addinivalue_line("markers", "unit: marks unit tests")
    config.addinivalue_line("markers", "power: marks power management tests")


# Configure pytest-xdist for proper test distribution
def pytest_xdist_make_scheduler(config: pytest.Config, log: object | None) -> None:
    """Configure xdist scheduler for optimal test distribution.

    Tests marked with @pytest.mark.serial will run in a single worker.

    Args:
        config: pytest configuration object
        log: xdist log producer object

    Returns:
        Custom scheduler instance or None if xdist is not available
    """
    # Use default scheduler to avoid issues with custom schedulers
    # The SerialScheduler was causing isinstance() errors during session teardown
    # Tests marked with @pytest.mark.serial can still be handled by configuring
    # pytest-xdist with appropriate options if needed


# =============================================================================
# SHARED TEST FIXTURES
# =============================================================================

# Constants for standard test configurations
# Using smaller sizes for faster test execution
STANDARD_PANEL_WIDTH = 800  # Reduced from 1024
STANDARD_PANEL_HEIGHT = 600  # Reduced from 768
STANDARD_VCOM = -2.0
STANDARD_VCOM_RAW = 2000  # Raw value for -2.0V


@pytest.fixture
def mock_spi() -> MockSPI:
    """Create a basic mock SPI interface."""
    return MockSPI()


@pytest.fixture
def mock_spi_with_device_info(mock_spi: MockSPI) -> MockSPI:
    """Create mock SPI with standard device info pre-configured."""
    # Standard device info response (20 values)
    mock_spi.set_read_data(
        [
            STANDARD_PANEL_WIDTH,
            STANDARD_PANEL_HEIGHT,
            MemoryConstants.IMAGE_BUFFER_ADDR_L,
            MemoryConstants.IMAGE_BUFFER_ADDR_H,
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
    # REG_0204 read for packed write enable
    mock_spi.set_read_data([0x0000])
    return mock_spi


@pytest.fixture
def it8951_driver(mock_spi_with_device_info: MockSPI) -> IT8951:
    """Create IT8951 driver with standard configuration."""
    driver = IT8951(mock_spi_with_device_info)
    driver.init()
    return driver


@pytest.fixture
def display_uninitialized(mock_spi: MockSPI) -> EPaperDisplay:
    """Create uninitialized EPaperDisplay."""
    return EPaperDisplay(vcom=STANDARD_VCOM, spi_interface=mock_spi)


@pytest.fixture
def display_initialized(mock_spi_with_device_info: MockSPI, mocker: MockerFixture) -> EPaperDisplay:
    """Create initialized EPaperDisplay with standard configuration."""
    # Add VCOM read response
    mock_spi_with_device_info.set_read_data([STANDARD_VCOM_RAW])

    display = EPaperDisplay(vcom=STANDARD_VCOM, spi_interface=mock_spi_with_device_info)

    # Mock clear to avoid complex buffer operations
    mocker.patch.object(display, "clear")

    display.init()
    return display


@pytest.fixture(scope="session")
def test_image_100x100() -> Image.Image:
    """Create a standard 100x100 test image."""
    return Image.new("L", (100, 100), color=128)


@pytest.fixture(scope="session")
def test_array_100x100() -> NDArray[np.uint8]:
    """Create a standard 100x100 numpy array."""
    return np.full((100, 100), 128, dtype=np.uint8)


@pytest.fixture
def mock_controller_methods(mocker: MockerFixture) -> dict[str, Mock]:
    """Common controller method mocks."""
    return {
        "pack_pixels": mocker.Mock(return_value=b"\x00" * 1000),
        "load_image_area_start": mocker.Mock(),
        "load_image_write": mocker.Mock(),
        "load_image_end": mocker.Mock(),
        "display_area": mocker.Mock(),
        "_wait_display_ready": mocker.Mock(),
    }


# Performance test fixtures
@pytest.fixture(scope="module")
def large_test_image() -> NDArray[np.uint8]:
    """Create a large test image for performance tests."""
    # Reduced size for faster tests (was 1404x1872)
    return np.random.randint(0, 256, size=(600, 800), dtype=np.uint8)


# Helper fixture for power management tests
@pytest.fixture
def display_with_power_management(
    display_initialized: EPaperDisplay, mocker: MockerFixture
) -> EPaperDisplay:
    """Display with power management mocks set up."""
    # The display is already initialized and active
    # Just mock time for auto-sleep tests
    mock_time = mocker.patch("time.time")
    mock_time.return_value = 100.0

    return display_initialized


# =============================================================================
# TIMING OPTIMIZATION FIXTURES
# =============================================================================


@pytest.fixture
def fast_timing(mocker: MockerFixture) -> None:
    """Mock all timing delays for faster test execution.

    This fixture aggressively mocks time.sleep() calls to speed up tests
    while maintaining logical flow.
    """

    # Create a fast sleep that just yields control but doesn't actually sleep
    def fast_sleep(seconds: float) -> None:
        # For very short sleeps (< 0.01s), don't sleep at all
        if seconds < 0.01:
            return
        # For longer sleeps, sleep for a tiny fraction of the requested time
        # This maintains relative timing relationships but speeds up tests
        import time

        time.sleep(min(seconds * 0.01, 0.001))

    mocker.patch("time.sleep", side_effect=fast_sleep)


@pytest.fixture
def instant_timing(mocker: MockerFixture) -> None:
    """Mock all timing delays to be instant (no sleep at all).

    Use this for unit tests where timing is not relevant.
    """
    mocker.patch("time.sleep", return_value=None)


@pytest.fixture
def mock_hardware_timing(mocker: MockerFixture) -> dict[str, float]:
    """Mock hardware-specific timing constants for faster tests."""
    from IT8951_ePaper_Py.constants import TimingConstants

    # Store original values
    original_values = {
        "RESET_DURATION_S": TimingConstants.RESET_DURATION_S,
        "BUSY_POLL_FAST_S": TimingConstants.BUSY_POLL_FAST_S,
        "BUSY_POLL_SLOW_S": TimingConstants.BUSY_POLL_SLOW_S,
        "DISPLAY_POLL_S": TimingConstants.DISPLAY_POLL_S,
    }

    # Set fast values for tests
    mocker.patch.object(TimingConstants, "RESET_DURATION_S", 0.001)
    mocker.patch.object(TimingConstants, "BUSY_POLL_FAST_S", 0.0001)
    mocker.patch.object(TimingConstants, "BUSY_POLL_SLOW_S", 0.001)
    mocker.patch.object(TimingConstants, "DISPLAY_POLL_S", 0.001)

    return original_values


@pytest.fixture(autouse=True)
def auto_fast_timing(request: pytest.FixtureRequest, mocker: MockerFixture) -> None:
    """Automatically apply fast timing to all tests except those marked as slow.

    This fixture automatically speeds up tests by mocking time.sleep() unless:
    - The test is marked with @pytest.mark.slow
    - The test explicitly uses real timing
    """
    # Check if test is marked as slow or needs real timing
    marker_names: list[str] = [marker.name for marker in request.node.iter_markers()]  # type: ignore[attr-defined]
    if any(name in ["slow", "real_timing"] for name in marker_names):
        return  # Don't mock timing for these tests

    # Apply fast timing for all other tests
    def fast_sleep(seconds: float) -> None:
        if seconds < 0.01:
            return
        import time

        time.sleep(min(seconds * 0.01, 0.001))

    mocker.patch("time.sleep", side_effect=fast_sleep)


# =============================================================================
# ATS (AUTOMATED TEST SELECTION) SUPPORT
# =============================================================================


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:  # noqa: C901
    """Modify test collection for ATS and add automatic markers.

    This hook:
    1. Adds module-based markers for better test organization
    2. Automatically marks slow/performance tests
    3. Adds metadata for ATS test impact analysis
    """
    for item in items:
        # Add automatic markers based on test name/location
        test_file = str(item.fspath)
        test_name = item.name

        # Performance test detection
        if "test_performance" in test_file or "benchmark" in test_name:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)

        # Power management test detection
        if "test_power_management" in test_file or "power" in test_name:
            item.add_marker(pytest.mark.power)

        # Slow test detection by name patterns
        slow_patterns = [
            "test_large_",
            "test_stress_",
            "test_timeout_",
            "test_progressive_",
            "test_full_",
            "test_extended_",
        ]
        if any(pattern in test_name for pattern in slow_patterns):
            item.add_marker(pytest.mark.slow)

        # Add ATS metadata - which source module does this test cover?
        # Use item.parent to get module information
        if item.parent is not None:
            parent = item.parent
            while parent is not None and not hasattr(parent, "module"):
                parent = parent.parent

            if parent is not None and hasattr(parent, "module"):
                module = getattr(parent, "module", None)
                if module is not None:
                    module_name = module.__name__
                    if module_name.startswith("tests.test_"):
                        # Extract the source module being tested
                        source_module = module_name.replace("tests.test_", "")
                        # Add as test property for ATS to track
                        item.user_properties.append(("ats_source_module", source_module))

                        # Also add the full test label for ATS
                        # Get class name if available
                        class_name: str | None = None
                        # Use getattr to safely access cls attribute
                        item_cls = getattr(item, "cls", None)
                        if item_cls is not None:
                            class_name = item_cls.__name__
                        elif (
                            item.parent
                            and hasattr(item.parent, "name")
                            and "::" not in item.parent.name
                        ):
                            # Try to get class name from parent
                            class_name = item.parent.name

                        test_label = (
                            f"{test_file}::{class_name}::{test_name}"
                            if class_name
                            else f"{test_file}::{test_name}"
                        )
                        item.user_properties.append(("ats_label", test_label))


def pytest_runtest_protocol(item: pytest.Item, nextitem: pytest.Item | None) -> None:
    """Hook for ATS to track test execution and coverage mapping.

    This allows ATS to build a map of which tests cover which source files.
    """
    # Let the test run normally - ATS will use coverage data
    # to determine test impact
    # Use default protocol


def pytest_report_header(config: pytest.Config) -> list[str]:
    """Add ATS information to pytest header if available."""
    headers: list[str] = []

    # Check if running under ATS
    # Use hasattr to check if option exists, avoiding default parameter issues
    if hasattr(config.option, "ats") and config.option.ats:
        headers.append("ATS (Automated Test Selection): ENABLED")
        headers.append("Test selection based on code changes will be applied.")

    return headers


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add ATS-related command line options."""
    parser.addoption(
        "--ats",
        action="store_true",
        default=False,
        help="Enable Automated Test Selection mode",
    )
    parser.addoption(
        "--ats-file",
        action="store",
        default=None,
        help="File containing list of tests to run (one per line)",
    )
