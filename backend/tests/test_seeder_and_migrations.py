"""Tests for Database Seeder and Alembic Migration structures."""

import pytest
from app.models.tenant import Tenant, Office
from app.models.employee import Employee, Department
from app.models.field_visit import ClientDestination
from app.models.travel import Vehicle, TravelLog
from app.core.database import Base


def test_models_in_metadata():
    """Verify all 18 tables are properly registered in Base.metadata for migrations and seeding."""
    table_names = list(Base.metadata.tables.keys())
    
    expected_tables = [
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
    ]
    
    for tbl in expected_tables:
        assert tbl in table_names, f"Table {tbl} not found in Base.metadata!"


def test_seed_data_syntax_and_imports():
    """Ensure seed_data and init_db scripts can be loaded without syntax or symbol errors."""
    import importlib
    init_db_module = importlib.import_module("scripts.init_db")
    seed_data_module = importlib.import_module("scripts.seed_data")
    
    assert hasattr(init_db_module, "init_database")
    assert hasattr(seed_data_module, "seed")
