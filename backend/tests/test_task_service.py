"""Unit tests for task tracking business logic and attendance gating."""

import pytest
from app.services.task_service import format_seconds


def test_format_seconds():
    """Verify human-readable format conversion."""
    assert format_seconds(0) == "0m"
    assert format_seconds(59) == "0m"
    assert format_seconds(60) == "1m"
    assert format_seconds(3600) == "1h 0m"
    assert format_seconds(5400) == "1h 30m"
    assert format_seconds(9020) == "2h 30m"
