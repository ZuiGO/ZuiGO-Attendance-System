"""Unit tests for vehicle mileage calculation and odometer anti-fraud detection."""

import pytest
from app.services.travel_service import calculate_mileage_reimbursement, check_odometer_discrepancy


def test_mileage_reimbursement_calculation():
    """Verify reimbursement formulas for different transport modes."""
    # Personal Car @ ₹8.00/km for 45.5 km
    assert calculate_mileage_reimbursement("PERSONAL_CAR", 45.5, 8.00) == 364.00

    # Two Wheeler @ ₹4.00/km for 22.0 km
    assert calculate_mileage_reimbursement("TWO_WHEELER", 22.0, 4.00) == 88.00

    # Company Car (no per-km reimbursement; fuel card provided)
    assert calculate_mileage_reimbursement("COMPANY_CAR", 120.0, 8.00) == 0.0

    # Walking (no reimbursement)
    assert calculate_mileage_reimbursement("WALKING", 5.0, 0.0) == 0.0


def test_odometer_discrepancy_normal_travel():
    """Verify normal small discrepancy between odometer and GPS (< 15%) is NOT flagged."""
    # Odometer: 42.0 km, GPS: 40.5 km (3.57% difference)
    pct, is_flagged = check_odometer_discrepancy(odometer_km=42.0, gps_km=40.5, threshold_pct=15.0)
    assert pct == 3.57
    assert is_flagged is False


def test_odometer_discrepancy_fraud_alert():
    """
    CRITICAL ANTI-FRAUD TEST:
    Verify that odometer reading exceeding GPS distance by > 15% triggers fraud flag.
    (e.g. Employee drives personal detour without tracking, or claims fake odometer)
    """
    # Odometer: 50.0 km, GPS: 32.0 km (36% gap!)
    pct, is_flagged = check_odometer_discrepancy(odometer_km=50.0, gps_km=32.0, threshold_pct=15.0)
    assert pct == 36.0
    assert is_flagged is True


def test_odometer_zero_or_negative():
    """Verify edge cases with zero odometer input."""
    pct, is_flagged = check_odometer_discrepancy(odometer_km=0.0, gps_km=10.0, threshold_pct=15.0)
    assert pct == 0.0
    assert is_flagged is False
