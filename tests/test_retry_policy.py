"""Tests for retry policy and mechanisms."""

from unittest.mock import Mock, patch

import pytest

from IT8951_ePaper_Py.exceptions import CommunicationError, IT8951TimeoutError
from IT8951_ePaper_Py.retry_policy import (
    BackoffStrategy,
    RetryPolicy,
    RetrySPIInterface,
    create_retry_spi_interface,
    with_retry,
)
from IT8951_ePaper_Py.spi_interface import MockSPI


class TestRetryPolicy:
    """Test RetryPolicy configuration."""

    def test_default_policy(self):
        """Test default retry policy values."""
        policy = RetryPolicy()
        assert policy.max_attempts == 3
        assert policy.delay == 0.1
        assert policy.backoff_factor == 2.0
        assert policy.exceptions == (CommunicationError, IT8951TimeoutError)

    def test_custom_policy(self):
        """Test custom retry policy values."""
        policy = RetryPolicy(
            max_attempts=5,
            delay=0.5,
            backoff_factor=1.5,
            exceptions=(ValueError, TypeError),
        )
        assert policy.max_attempts == 5
        assert policy.delay == 0.5
        assert policy.backoff_factor == 1.5
        assert policy.exceptions == (ValueError, TypeError)

    def test_invalid_max_attempts(self):
        """Test that invalid max_attempts raises error."""
        with pytest.raises(ValueError, match="max_attempts must be at least 1"):
            RetryPolicy(max_attempts=0)

    def test_invalid_delay(self):
        """Test that negative delay raises error."""
        with pytest.raises(ValueError, match="delay must be non-negative"):
            RetryPolicy(delay=-0.1)

    def test_invalid_backoff_factor(self):
        """Test that backoff_factor < 1 raises error."""
        with pytest.raises(ValueError, match="backoff_factor must be at least 1.0"):
            RetryPolicy(backoff_factor=0.5)

    def test_invalid_max_delay(self):
        """Test that max_delay < delay raises error."""
        with pytest.raises(ValueError, match="max_delay must be at least as large as delay"):
            RetryPolicy(delay=1.0, max_delay=0.5)

    def test_invalid_jitter_range(self):
        """Test that jitter_range outside 0-1 raises error."""
        with pytest.raises(ValueError, match="jitter_range must be between 0.0 and 1.0"):
            RetryPolicy(jitter_range=1.5)

    def test_backoff_strategies(self):
        """Test different backoff strategies."""
        # Test default (exponential)
        policy = RetryPolicy()
        assert policy.backoff_strategy == BackoffStrategy.EXPONENTIAL

        # Test all strategies are accepted
        for strategy in BackoffStrategy:
            policy = RetryPolicy(backoff_strategy=strategy)
            assert policy.backoff_strategy == strategy

    def test_calculate_delay_fixed(self):
        """Test fixed backoff strategy."""
        policy = RetryPolicy(delay=0.5, backoff_strategy=BackoffStrategy.FIXED)
        assert policy.calculate_delay(0) == 0.5
        assert policy.calculate_delay(1) == 0.5
        assert policy.calculate_delay(5) == 0.5

    def test_calculate_delay_linear(self):
        """Test linear backoff strategy."""
        policy = RetryPolicy(delay=0.1, backoff_strategy=BackoffStrategy.LINEAR)
        assert policy.calculate_delay(0) == 0.1  # 0.1 * (0+1)
        assert policy.calculate_delay(1) == 0.2  # 0.1 * (1+1)
        assert abs(policy.calculate_delay(2) - 0.3) < 0.001  # 0.1 * (2+1) with float tolerance

    def test_calculate_delay_exponential(self):
        """Test exponential backoff strategy."""
        policy = RetryPolicy(
            delay=0.1, backoff_factor=2.0, backoff_strategy=BackoffStrategy.EXPONENTIAL
        )
        assert policy.calculate_delay(0) == 0.1  # 0.1 * 2^0
        assert policy.calculate_delay(1) == 0.2  # 0.1 * 2^1
        assert policy.calculate_delay(2) == 0.4  # 0.1 * 2^2

    def test_calculate_delay_with_max_delay(self):
        """Test that max_delay caps the calculated delay."""
        policy = RetryPolicy(
            delay=1.0,
            backoff_factor=10.0,
            max_delay=5.0,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
        )
        assert policy.calculate_delay(0) == 1.0  # 1.0 * 10^0
        assert policy.calculate_delay(1) == 5.0  # 10.0 capped at 5.0
        assert policy.calculate_delay(2) == 5.0  # 100.0 capped at 5.0

    def test_calculate_delay_jitter(self):
        """Test jitter backoff strategy."""
        policy = RetryPolicy(
            delay=1.0, backoff_factor=2.0, jitter_range=0.1, backoff_strategy=BackoffStrategy.JITTER
        )

        # Run multiple times to test randomness
        delays = [policy.calculate_delay(1) for _ in range(10)]

        # All delays should be around 2.0 +/- 0.2 (10% jitter of 2.0)
        for delay in delays:
            assert 1.8 <= delay <= 2.2

        # Delays should not all be the same (testing randomness)
        assert len(set(delays)) > 1


class TestWithRetry:
    """Test the with_retry decorator."""

    def test_successful_on_first_attempt(self):
        """Test function that succeeds on first attempt."""
        mock_func = Mock(return_value="success")
        policy = RetryPolicy(max_attempts=3)

        decorated = with_retry(policy)(mock_func)
        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_on_failure(self):
        """Test function that fails then succeeds."""
        mock_func = Mock(side_effect=[CommunicationError("fail"), "success"])
        policy = RetryPolicy(max_attempts=3, delay=0.01)

        decorated = with_retry(policy)(mock_func)
        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2

    def test_exhaust_retries(self):
        """Test function that exhausts all retries."""
        mock_func = Mock(side_effect=CommunicationError("fail"))
        policy = RetryPolicy(max_attempts=3, delay=0.01)

        decorated = with_retry(policy)(mock_func)

        with pytest.raises(CommunicationError, match="fail"):
            decorated()

        assert mock_func.call_count == 3

    def test_retry_with_backoff(self):
        """Test that backoff factor is applied correctly."""
        mock_func = Mock(
            side_effect=[CommunicationError("fail"), CommunicationError("fail"), "success"]
        )
        policy = RetryPolicy(max_attempts=3, delay=0.01, backoff_factor=2.0)

        # Mock time.sleep to verify delay values
        with patch("IT8951_ePaper_Py.retry_policy.time.sleep") as mock_sleep:
            decorated = with_retry(policy)(mock_func)
            result = decorated()

        assert result == "success"
        assert mock_func.call_count == 3

        # Verify sleep was called with correct delays
        assert mock_sleep.call_count == 2
        # First retry uses calculate_delay(0) = 0.01 * 2^0 = 0.01
        # Second retry uses calculate_delay(1) = 0.01 * 2^1 = 0.02
        calls = mock_sleep.call_args_list
        assert calls[0][0][0] == 0.01  # First retry
        assert calls[1][0][0] == 0.02  # Second retry with backoff

    def test_retry_with_different_strategies(self):
        """Test retry with different backoff strategies."""
        # Test with fixed strategy
        mock_func = Mock(side_effect=[CommunicationError("fail"), "success"])
        policy = RetryPolicy(max_attempts=2, delay=0.05, backoff_strategy=BackoffStrategy.FIXED)

        with patch("IT8951_ePaper_Py.retry_policy.time.sleep") as mock_sleep:
            decorated = with_retry(policy)(mock_func)
            result = decorated()

        assert result == "success"
        mock_sleep.assert_called_once_with(0.05)

        # Test with linear strategy
        mock_func = Mock(
            side_effect=[CommunicationError("fail"), CommunicationError("fail"), "success"]
        )
        policy = RetryPolicy(max_attempts=3, delay=0.01, backoff_strategy=BackoffStrategy.LINEAR)

        with patch("IT8951_ePaper_Py.retry_policy.time.sleep") as mock_sleep:
            decorated = with_retry(policy)(mock_func)
            result = decorated()

        assert result == "success"
        calls = mock_sleep.call_args_list
        assert calls[0][0][0] == 0.01  # 0.01 * 1
        assert calls[1][0][0] == 0.02  # 0.01 * 2

    def test_only_retry_specified_exceptions(self):
        """Test that only specified exceptions are retried."""
        mock_func = Mock(side_effect=ValueError("not retryable"))
        policy = RetryPolicy(max_attempts=3, exceptions=(CommunicationError,))

        decorated = with_retry(policy)(mock_func)

        with pytest.raises(ValueError, match="not retryable"):
            decorated()

        assert mock_func.call_count == 1  # No retries

    def test_preserve_function_metadata(self):
        """Test that decorator preserves function metadata."""

        @with_retry(RetryPolicy())
        def example_function(x: int, y: int) -> int:
            """Example function docstring."""
            return x + y

        assert example_function.__name__ == "example_function"
        assert example_function.__doc__ == "Example function docstring."


class TestRetrySPIInterface:
    """Test RetrySPIInterface wrapper."""

    @pytest.fixture
    def mock_spi(self):
        """Create a mock SPI interface."""
        return MockSPI()

    @pytest.fixture
    def retry_spi(self, mock_spi):
        """Create a retry SPI interface with short delays."""
        policy = RetryPolicy(max_attempts=3, delay=0.01)
        return RetrySPIInterface(mock_spi, policy)

    def test_init_success(self, retry_spi):
        """Test successful initialization."""
        retry_spi.init()
        # Should succeed without issues

    def test_init_retry(self, mocker):
        """Test initialization with retry."""
        mock_spi = Mock()
        mock_spi.init.side_effect = [CommunicationError("fail"), None]

        policy = RetryPolicy(max_attempts=3, delay=0.01)
        retry_spi = RetrySPIInterface(mock_spi, policy)

        retry_spi.init()

        assert mock_spi.init.call_count == 2

    def test_write_command_retry(self, mocker):
        """Test write_command with retry."""
        mock_spi = Mock()
        mock_spi.write_command.side_effect = [CommunicationError("fail"), None]

        policy = RetryPolicy(max_attempts=3, delay=0.01)
        retry_spi = RetrySPIInterface(mock_spi, policy)

        retry_spi.write_command(0x10)

        assert mock_spi.write_command.call_count == 2
        mock_spi.write_command.assert_called_with(0x10)

    def test_read_data_retry(self, mocker):
        """Test read_data with retry."""
        mock_spi = Mock()
        mock_spi.read_data.side_effect = [CommunicationError("fail"), 0x1234]

        policy = RetryPolicy(max_attempts=3, delay=0.01)
        retry_spi = RetrySPIInterface(mock_spi, policy)

        result = retry_spi.read_data()

        assert result == 0x1234
        assert mock_spi.read_data.call_count == 2

    def test_write_data_bulk_retry(self, mocker):
        """Test write_data_bulk with retry."""
        mock_spi = Mock()
        mock_spi.write_data_bulk.side_effect = [CommunicationError("fail"), None]

        policy = RetryPolicy(max_attempts=3, delay=0.01)
        retry_spi = RetrySPIInterface(mock_spi, policy)

        data = [0x1234, 0x5678]
        retry_spi.write_data_bulk(data)

        assert mock_spi.write_data_bulk.call_count == 2
        mock_spi.write_data_bulk.assert_called_with(data)

    def test_wait_busy_no_retry_on_timeout(self, mocker):
        """Test that wait_busy doesn't retry on timeout errors."""
        mock_spi = Mock()
        mock_spi.wait_busy.side_effect = IT8951TimeoutError("timeout")

        policy = RetryPolicy(max_attempts=3, delay=0.01)
        retry_spi = RetrySPIInterface(mock_spi, policy)

        with pytest.raises(IT8951TimeoutError, match="timeout"):
            retry_spi.wait_busy(1000)

        # Should not retry timeout errors
        assert mock_spi.wait_busy.call_count == 1

    def test_wait_busy_retry_on_communication_error(self, mocker):
        """Test that wait_busy retries on communication errors."""
        mock_spi = Mock()
        mock_spi.wait_busy.side_effect = [CommunicationError("fail"), None]

        policy = RetryPolicy(max_attempts=3, delay=0.01)
        retry_spi = RetrySPIInterface(mock_spi, policy)

        retry_spi.wait_busy(1000)

        assert mock_spi.wait_busy.call_count == 2

    def test_close_no_retry(self, mocker):
        """Test that close doesn't use retry logic."""
        mock_spi = Mock()
        mock_spi.close.side_effect = Exception("fail")

        policy = RetryPolicy(max_attempts=3)
        retry_spi = RetrySPIInterface(mock_spi, policy)

        with pytest.raises(Exception, match="fail"):
            retry_spi.close()

        # Close should not retry
        assert mock_spi.close.call_count == 1

    def test_reset_retry(self, mocker):
        """Test reset() method with retry logic."""
        mock_spi = Mock()
        mock_spi.reset.side_effect = [CommunicationError("fail"), None]

        policy = RetryPolicy(max_attempts=3, delay=0.01)
        retry_spi = RetrySPIInterface(mock_spi, policy)

        retry_spi.reset()

        assert mock_spi.reset.call_count == 2

    def test_write_data_retry(self, mocker):
        """Test write_data() method with retry logic."""
        mock_spi = Mock()
        mock_spi.write_data.side_effect = [CommunicationError("fail"), None]

        policy = RetryPolicy(max_attempts=3, delay=0.01)
        retry_spi = RetrySPIInterface(mock_spi, policy)

        retry_spi.write_data(0xABCD)

        assert mock_spi.write_data.call_count == 2
        mock_spi.write_data.assert_called_with(0xABCD)

    def test_read_data_bulk_retry(self, mocker):
        """Test read_data_bulk() method with retry logic."""
        mock_spi = Mock()
        expected_data = [0x12, 0x34, 0x56, 0x78]
        mock_spi.read_data_bulk.side_effect = [CommunicationError("fail"), expected_data]

        policy = RetryPolicy(max_attempts=3, delay=0.01)
        retry_spi = RetrySPIInterface(mock_spi, policy)

        result = retry_spi.read_data_bulk(4)

        assert result == expected_data
        assert mock_spi.read_data_bulk.call_count == 2
        mock_spi.read_data_bulk.assert_called_with(4)


class TestCreateRetrySPIInterface:
    """Test the factory function."""

    def test_create_with_defaults(self, mocker):
        """Test creation with default parameters."""
        # Mock the create_spi_interface function
        mock_create = mocker.patch(
            "IT8951_ePaper_Py.spi_interface.create_spi_interface",
            return_value=MockSPI(),
        )

        spi = create_retry_spi_interface()

        assert isinstance(spi, RetrySPIInterface)
        mock_create.assert_called_once_with(spi_speed_hz=None)

    def test_create_with_custom_policy(self):
        """Test creation with custom retry policy."""
        base_spi = MockSPI()
        policy = RetryPolicy(max_attempts=5, delay=0.2)

        spi = create_retry_spi_interface(spi_interface=base_spi, retry_policy=policy)

        assert isinstance(spi, RetrySPIInterface)
        assert spi._policy == policy

    def test_create_with_spi_speed(self, mocker):
        """Test creation with SPI speed override."""
        mock_create = mocker.patch(
            "IT8951_ePaper_Py.spi_interface.create_spi_interface",
            return_value=MockSPI(),
        )

        spi = create_retry_spi_interface(spi_speed_hz=2000000)

        assert isinstance(spi, RetrySPIInterface)
        mock_create.assert_called_once_with(spi_speed_hz=2000000)
