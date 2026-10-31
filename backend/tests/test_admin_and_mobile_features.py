"""Senior QA Tests for Admin Employee CRUD, Task Assignment, Live Presence with Network Indicators, Location Ping, and Activity Audit Trails."""

from datetime import datetime, timezone
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.attendance import AttendanceRecord
from app.models.employee import Department, Employee
from app.models.tenant import Office
from app.models.task import Project, Task, TaskTimeEntry
from app.schemas.admin import (
    AssignTaskRequest,
    CreateEmployeeRequest,
    LiveEmployeePresence,
    LivePresenceBoardResponse,
)
from app.schemas.attendance import LocationPingRequest
from app.services.activity_service import ActivityService
from app.services.admin_service import AdminDashboardService
from app.services.attendance_service import AttendanceVerificationService


@pytest.mark.asyncio
async def test_admin_create_and_delete_employee():
    """Verify Admin can add a new employee and soft-delete/deactivate them."""
    db = AsyncMock()
    service = AdminDashboardService(db=db)
    tenant_id = uuid.uuid4()

    # Mocks for uniqueness checks (None means no collision)
    db.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: None),  # email check
        MagicMock(scalar_one_or_none=lambda: None),  # code check
        MagicMock(scalar_one_or_none=lambda: None),  # dept check
        MagicMock(scalar_one_or_none=lambda: None),  # office check
    ]

    req = CreateEmployeeRequest(
        full_name="Karan Malhotra",
        email="karan.m@zuigo.ai",
        password="secretpassword123",
        employee_code="EMP-2001",
        role="EMPLOYEE",
        department_name="Field Operations",
        phone="+919876500000",
    )

    success, error_msg, emp_item = await service.create_employee(tenant_id, req)
    assert success is True
    assert emp_item is not None
    assert emp_item.full_name == "Karan Malhotra"
    assert emp_item.email == "karan.m@zuigo.ai"
    assert emp_item.employee_code == "EMP-2001"
    assert emp_item.is_active is True

    # Test Deactivation / Delete
    mock_emp = MagicMock(spec=Employee)
    mock_emp.id = uuid.uuid4()
    mock_emp.tenant_id = tenant_id
    mock_emp.full_name = "Karan Malhotra"
    mock_emp.employee_code = "EMP-2001"
    mock_emp.is_active = True

    db.get.return_value = mock_emp
    db.execute.side_effect = None
    db.execute.return_value = MagicMock(scalars=lambda: MagicMock(all=lambda: []))

    del_success, del_err = await service.delete_employee(tenant_id, mock_emp.id)
    assert del_success is True
    assert mock_emp.is_active is False


@pytest.mark.asyncio
async def test_admin_assign_task_to_employee():
    """Verify Admin can assign a new task to an employee."""
    db = AsyncMock()
    service = AdminDashboardService(db=db)
    tenant_id = uuid.uuid4()
    emp_id = uuid.uuid4()

    mock_emp = MagicMock(spec=Employee)
    mock_emp.id = emp_id
    mock_emp.tenant_id = tenant_id
    mock_emp.full_name = "Priya Sharma"

    mock_proj = MagicMock(spec=Project)
    mock_proj.id = uuid.uuid4()
    mock_proj.name = "Hospital Relations"

    db.get.side_effect = [mock_emp, mock_proj]
    db.execute.return_value = MagicMock(scalar_one_or_none=lambda: mock_proj)

    req = AssignTaskRequest(
        title="Emergency Ward Sensor Diagnostic",
        description="Verify IoT heartbeat telemetry at Apollo Hospital",
        assigned_to=str(emp_id),
        priority="HIGH",
        estimated_hours=2.5,
    )

    success, error_msg, task_item = await service.assign_task(tenant_id, req)
    assert success is True
    assert task_item is not None
    assert task_item.title == "Emergency Ward Sensor Diagnostic"
    assert task_item.assigned_to_name == "Priya Sharma"
    assert task_item.priority == "HIGH"
    assert task_item.status == "TODO"


@pytest.mark.asyncio
async def test_attendance_ping_location_telemetry():
    """Verify mobile app location ping streams GPS telemetry to database."""
    db = AsyncMock()
    qr_service = AsyncMock()
    service = AttendanceVerificationService(db=db, qr_service=qr_service)
    tenant_id = uuid.uuid4()
    emp_id = uuid.uuid4()

    mock_emp = MagicMock(spec=Employee)
    mock_emp.id = emp_id
    db.get.return_value = mock_emp

    req = LocationPingRequest(
        latitude=28.4986,
        longitude=77.0878,
        accuracy_meters=4.2,
        is_mock=False,
        network_type="OFFICE_WIFI",
        wifi_bssid="3c:37:12:89:af:90",
    )

    res = await service.ping_location(emp_id, tenant_id, req)
    assert res["status"] == "RECORDED"
    assert res["latitude"] == 28.4986
    assert res["longitude"] == 77.0878
    assert res["network_type"] == "OFFICE_WIFI"
    assert mock_emp.last_known_latitude == 28.4986
    assert mock_emp.last_known_longitude == 77.0878


@pytest.mark.asyncio
async def test_user_activity_audit_logging():
    """Verify ActivityService records structured audit entries with network type and coordinates."""
    db = AsyncMock()
    service = ActivityService(db=db)
    tenant_id = uuid.uuid4()
    emp_id = uuid.uuid4()

    log_entry = await service.log_activity(
        tenant_id=tenant_id,
        employee_id=emp_id,
        activity_type="FIELD_VISIT_OTP_VERIFIED",
        description="Customer Dr. K. Mehta verified OTP 4921 at Apollo City Hospital",
        network_type="PERSONAL_CELLULAR",
        is_office_wifi=False,
        ip_address="192.168.1.127",
        location_latitude=28.5355,
        location_longitude=77.3910,
        metadata_json={"otp_code": "4921", "client_name": "Apollo City Hospital"},
    )

    assert log_entry.activity_type == "FIELD_VISIT_OTP_VERIFIED"
    assert log_entry.is_office_wifi is False
    assert log_entry.network_type == "PERSONAL_CELLULAR"
    assert log_entry.location_latitude == 28.5355
    assert log_entry.metadata_json["otp_code"] == "4921"
