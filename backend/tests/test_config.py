"""Unit tests for system configuration and settings."""

import pytest
from app.core.config import Settings


def test_default_settings():
    """Verify system defaults adhere to project plan specifications."""
    s = Settings()
    assert s.DEFAULT_FIELD_DWELL_MINUTES == 30
    assert s.QR_CODE_TTL_SECONDS == 15
    assert s.QR_SKEW_TOLERANCE_SECONDS == 5
    assert s.OTP_TTL_SECONDS == 300
    assert s.OTP_MAX_ATTEMPTS == 3
    assert s.ODOMETER_DISCREPANCY_THRESHOLD_PCT == 15.0
    assert s.REIMBURSEMENT_RATES["PERSONAL_CAR"] == 8.00
    assert s.REIMBURSEMENT_RATES["TWO_WHEELER"] == 4.00
    assert s.JWT_ALGORITHM == "HS256"
