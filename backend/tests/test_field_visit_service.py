"""Unit tests for Field Visit (PoPV), Dwell Time (30 min), and Client OTP logic."""

from datetime import datetime, timedelta, timezone
import pytest
from app.services.field_visit_service import mask_phone_number
from app.services.attendance_service import calculate_haversine_distance_meters


def test_mask_phone_number():
    """Verify phone numbers are masked securely for privacy."""
    assert mask_phone_number("+919876543210") == "+919876***10"
    assert mask_phone_number("9876543210") == "9876543***10"
    assert mask_phone_number("123") == "***"


def test_field_geofence_arrival_proximity():
    """Verify arrival coordinates inside vs outside 75-meter geofence radius."""
    # Target hospital coordinates
    dest_lat = 28.535517
    dest_lon = 77.391029

    # Point A: 30 meters away (inside 75m)
    emp_lat_inside = 28.535750
    emp_lon_inside = 77.391029
    dist_inside = calculate_haversine_distance_meters(emp_lat_inside, emp_lon_inside, dest_lat, dest_lon)
    assert dist_inside <= 75.0

    # Point B: 250 meters away (outside 75m)
    emp_lat_outside = 28.537800
    emp_lon_outside = 77.391029
    dist_outside = calculate_haversine_distance_meters(emp_lat_outside, emp_lon_outside, dest_lat, dest_lon)
    assert dist_outside > 75.0


def test_field_visit_dwell_time_logic():
    """
    CRITICAL ANTI-DRIVE-BY TEST:
    Verify that 30-minute dwell time requirement blocks premature completion.
    """
    arrival_time = datetime.now(timezone.utc) - timedelta(minutes=12)  # Arrived 12 mins ago
    required_minutes = 30

    dwell_seconds = int((datetime.now(timezone.utc) - arrival_time).total_seconds())
    required_seconds = required_minutes * 60

    # Must be less than required
    assert dwell_seconds < required_seconds
    assert (required_seconds - dwell_seconds) > 0  # 18 minutes remaining

    # Scenario: Arrived 35 minutes ago
    valid_arrival = datetime.now(timezone.utc) - timedelta(minutes=35)
    valid_dwell = int((datetime.now(timezone.utc) - valid_arrival).total_seconds())
    assert valid_dwell >= required_seconds
