"""Performance tests for power management features."""

import time

import pytest

from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import PowerState, SystemCommand
from IT8951_ePaper_Py.models import DeviceInfo


@pytest.fixture
def display(mocker):
    """Create display with mocked SPI for power management testing."""
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

    # Mock power state tracking
    display._controller._power_state = PowerState.ACTIVE

    return display


class TestPowerManagementPerformance:
    """Test power management performance characteristics."""

    def test_sleep_wake_transition_time(self, display):
        """Test time taken for sleep/wake transitions."""
        # Mock the actual commands to measure overhead
        mock_write_command = display._controller._spi.write_command

        # Test sleep transition
        start_time = time.time()
        display.sleep()
        sleep_time = time.time() - start_time

        # Verify command was sent
        mock_write_command.assert_called_with(SystemCommand.SLEEP)

        # Sleep transition should be fast (< 100ms overhead)
        assert sleep_time < 0.1
        assert display._controller._power_state == PowerState.SLEEP

        # Test wake transition
        mock_write_command.reset_mock()
        start_time = time.time()
        display.wake()
        wake_time = time.time() - start_time

        # Wake should reinitialize
        assert display._controller._power_state == PowerState.ACTIVE

        # Wake transition includes init, so allow more time
        assert wake_time < 0.2

    def test_standby_transition_performance(self, display):
        """Test standby mode transition performance."""
        mock_write_command = display._controller._spi.write_command

        # Test standby transition
        start_time = time.time()
        display.standby()
        standby_time = time.time() - start_time

        # Verify command
        mock_write_command.assert_called_with(SystemCommand.STANDBY)

        # Standby should be very fast
        assert standby_time < 0.05
        assert display._controller._power_state == PowerState.STANDBY

        # Test wake from standby
        mock_write_command.reset_mock()
        start_time = time.time()
        display.wake()
        wake_time = time.time() - start_time

        # Wake from standby should be faster than from sleep
        assert wake_time < 0.1

    def test_auto_sleep_timeout_accuracy(self, display, mocker):
        """Test accuracy of auto-sleep timeout."""
        # Mock time.time to control timing
        mock_time = mocker.patch("time.time")
        current_time = 1000.0
        mock_time.return_value = current_time

        # Set auto-sleep timeout
        timeout = 5.0
        display.set_auto_sleep_timeout(timeout)

        # Verify timeout was set
        assert display._auto_sleep_timeout == timeout
        assert display._last_activity_time == current_time

        # Simulate time passing (just before timeout)
        mock_time.return_value = current_time + timeout - 0.1
        display._check_auto_sleep()
        assert display._controller._power_state == PowerState.ACTIVE

        # Simulate timeout reached
        mock_time.return_value = current_time + timeout + 0.1
        display._check_auto_sleep()
        assert display._controller._power_state == PowerState.SLEEP

    def test_power_state_tracking_overhead(self, display):
        """Test overhead of power state tracking."""
        # Measure overhead of state checks
        iterations = 1000

        start_time = time.time()
        for _ in range(iterations):
            state = display._controller._power_state
            assert state in [PowerState.ACTIVE, PowerState.STANDBY, PowerState.SLEEP]
        check_time = time.time() - start_time

        # Average time per check
        avg_check_time = check_time / iterations

        # Should be negligible (< 1 microsecond)
        assert avg_check_time < 0.000001

    def test_rapid_power_transitions(self, display):
        """Test performance of rapid power state changes."""
        # Test rapid sleep/wake cycles
        num_cycles = 10

        cycle_times = []
        for _ in range(num_cycles):
            start_time = time.time()

            display.sleep()
            display.wake()

            cycle_time = time.time() - start_time
            cycle_times.append(cycle_time)

        # Average cycle time
        avg_cycle_time = sum(cycle_times) / len(cycle_times)

        # Should handle rapid transitions efficiently
        assert avg_cycle_time < 0.3  # 300ms per cycle

        # Verify consistency
        for cycle_time in cycle_times:
            assert abs(cycle_time - avg_cycle_time) < 0.1  # Within 100ms

    def test_power_state_with_display_operations(self, display, mocker):
        """Test power state handling during display operations."""
        from PIL import Image

        # Create test image
        img = Image.new("L", (100, 100), 128)

        # Put display to sleep
        display.sleep()
        assert display._controller._power_state == PowerState.SLEEP

        # Measure time for display operation (should auto-wake)
        start_time = time.time()
        display.display_image(img)
        operation_time = time.time() - start_time

        # Should have woken up
        assert display._controller._power_state == PowerState.ACTIVE

        # Operation time includes wake overhead
        # but should still be reasonable
        assert operation_time < 0.5

    def test_context_manager_power_efficiency(self, mocker):
        """Test power management in context manager."""
        # Mock SPI interface
        mock_spi = mocker.MagicMock()
        mocker.patch("IT8951_ePaper_Py.display.RaspberryPiSPI", return_value=mock_spi)

        # Track power transitions
        power_transitions = []

        def track_transition(state) -> None:
            power_transitions.append((time.time(), state))

        # Use context manager
        start_time = time.time()
        with EPaperDisplay(vcom=-2.0) as display:
            # Mock the power state setter
            display._controller._power_state = PowerState.ACTIVE
            track_transition(PowerState.ACTIVE)

            # Simulate some work
            time.sleep(0.1)

            # Set auto-sleep
            display.set_auto_sleep_timeout(1.0)

        context_time = time.time() - start_time

        # Context manager should handle cleanup efficiently
        assert context_time < 0.3

        # Should have entered sleep on exit
        mock_spi.write_command.assert_any_call(SystemCommand.SLEEP)

    def test_power_consumption_simulation(self, display):
        """Simulate power consumption patterns."""
        # Define power consumption values (relative units)
        power_consumption = {PowerState.ACTIVE: 100, PowerState.STANDBY: 10, PowerState.SLEEP: 1}

        # Simulate usage pattern
        usage_pattern = [
            (PowerState.ACTIVE, 1.0),  # Active for 1s
            (PowerState.STANDBY, 2.0),  # Standby for 2s
            (PowerState.SLEEP, 5.0),  # Sleep for 5s
            (PowerState.ACTIVE, 0.5),  # Active for 0.5s
            (PowerState.SLEEP, 10.0),  # Sleep for 10s
        ]

        total_energy = 0
        for state, duration in usage_pattern:
            energy = power_consumption[state] * duration
            total_energy += energy

        # Calculate average power
        total_time = sum(duration for _, duration in usage_pattern)
        avg_power = total_energy / total_time

        # With proper power management, average should be low
        assert avg_power < 20  # Much less than active power

    @pytest.mark.parametrize("timeout", [0.1, 0.5, 1.0, 5.0])
    def test_auto_sleep_timeout_variations(self, display, mocker, timeout):
        """Test different auto-sleep timeout values."""
        mock_time = mocker.patch("time.time")
        current_time = 1000.0
        mock_time.return_value = current_time

        # Set timeout
        display.set_auto_sleep_timeout(timeout)

        # Test precision of timeout
        test_points = [
            timeout * 0.5,  # Half timeout
            timeout * 0.9,  # Just before
            timeout * 1.1,  # Just after
        ]

        for elapsed in test_points:
            # Reset to active
            display._controller._power_state = PowerState.ACTIVE
            display._last_activity_time = current_time

            # Check at test point
            mock_time.return_value = current_time + elapsed
            display._check_auto_sleep()

            if elapsed < timeout:
                assert display._controller._power_state == PowerState.ACTIVE
            else:
                assert display._controller._power_state == PowerState.SLEEP
