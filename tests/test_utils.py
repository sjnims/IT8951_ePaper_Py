"""Tests for utils module."""

import logging

import pytest

from IT8951_ePaper_Py.utils import timed_operation


class TestTimedOperation:
    """Test the timed_operation decorator."""

    def test_successful_operation(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test timed operation with successful execution."""

        @timed_operation("test operation")
        def successful_op() -> str:
            return "success"

        with caplog.at_level(logging.DEBUG):
            result = successful_op()

        assert result == "success"
        assert "test operation completed" in caplog.text
        assert "ms" in caplog.text

    def test_operation_with_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test timed operation that raises an exception."""

        @timed_operation("failing operation")
        def failing_op() -> None:
            raise ValueError("Test error")

        # The operation should still raise the exception
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError, match="Test error"):
            failing_op()

        # Verify that the failure was logged
        assert "failing operation failed" in caplog.text
        assert "ms" in caplog.text

    def test_operation_with_args(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test timed operation with arguments."""

        @timed_operation("operation with args")
        def op_with_args(x: int, y: int, z: int = 3) -> int:
            return x + y + z

        with caplog.at_level(logging.DEBUG):
            result = op_with_args(1, 2, z=4)

        assert result == 7
        assert "operation with args completed" in caplog.text
