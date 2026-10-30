"""Unit tests for SQLAlchemy database models metadata and table registrations."""

from app.core.database import Base
import app.models  # Loads all models


def test_models_metadata_registration():
    """Verify all tables defined in docs/DATABASE_SCHEMA.md are registered in SQLAlchemy metadata."""
    expected_tables = {
        "tenants",
        "offices",
        "departments",
        "employees",
        "attendance_records",
        "projects",
        "tasks",
        "task_time_entries",
        "client_destinations",
        "field_itineraries",
        "field_visit_stops",
        "field_visit_proofs",
        "client_otp_verifications",
        "vehicles",
        "travel_logs",
        "travel_legs",
        "travel_expense_receipts",
        "location_breadcrumbs",
    }

    registered_tables = set(Base.metadata.tables.keys())
    missing_tables = expected_tables - registered_tables
    assert not missing_tables, f"Missing registered tables: {missing_tables}"


def test_tenant_columns():
    """Verify tenant model columns."""
    tenant_table = Base.metadata.tables["tenants"]
    assert "id" in tenant_table.c
    assert "name" in tenant_table.c
    assert "subdomain" in tenant_table.c
    assert "configuration" in tenant_table.c


def test_attendance_columns():
    """Verify attendance model contains verification audit columns."""
    attendance_table = Base.metadata.tables["attendance_records"]
    assert "clock_in_location" in attendance_table.c
    assert "clock_in_bssid" in attendance_table.c
    assert "clock_in_client_ip" in attendance_table.c
    assert "clock_in_device_id" in attendance_table.c
    assert "clock_in_face_similarity_score" in attendance_table.c


def test_field_visit_columns():
    """Verify field visit stops and destinations contain dwell time and geofence columns."""
    dest_table = Base.metadata.tables["client_destinations"]
    assert "min_dwell_minutes" in dest_table.c
    assert "geofence_radius_meters" in dest_table.c
    assert "otp_channel" in dest_table.c

    stop_table = Base.metadata.tables["field_visit_stops"]
    assert "is_dwell_time_satisfied" in stop_table.c
    assert "is_geofence_verified" in stop_table.c
    assert "check_in_distance_meters" in stop_table.c


def test_travel_and_mileage_columns():
    """Verify travel logs contain odometer and discrepancy tracking."""
    log_table = Base.metadata.tables["travel_logs"]
    assert "odometer_start_km" in log_table.c
    assert "odometer_end_km" in log_table.c
    assert "gps_total_distance_km" in log_table.c
    assert "is_discrepancy_flagged" in log_table.c
    assert "reimbursement_rate_per_km" in log_table.c
    assert "reimbursement_amount" in log_table.c
