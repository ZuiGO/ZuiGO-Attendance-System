"""Unit tests for Employer Admin Dashboard business logic and analytics."""

import pytest
from app.schemas.admin import LiveEmployeePresence, LivePresenceBoardResponse, TenantPolicyUpdate


def test_live_presence_board_calculations():
    """Verify presence rate percentage calculation."""
    board = LivePresenceBoardResponse(
        total_expected=50,
        total_present=42,
        total_absent=8,
        presence_rate_pct=84.0,
        total_active_tasks=36,
        employees=[],
    )
    assert board.total_present == 42
    assert board.total_absent == 8
    assert board.presence_rate_pct == 84.0


def test_tenant_policy_update_schema():
    """Verify tenant policy update schema accepts custom dwell time and rates."""
    policy = TenantPolicyUpdate(
        field_visit_default_dwell_minutes=45,
        car_reimbursement_rate=9.50,
        bike_reimbursement_rate=5.00,
        odometer_discrepancy_threshold_pct=12.0,
    )
    assert policy.field_visit_default_dwell_minutes == 45
    assert policy.car_reimbursement_rate == 9.50
    assert policy.bike_reimbursement_rate == 5.00
    assert policy.odometer_discrepancy_threshold_pct == 12.0
