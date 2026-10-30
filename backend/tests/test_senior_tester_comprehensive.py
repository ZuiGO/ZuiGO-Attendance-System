"""Senior QA Comprehensive Verification Suite:
Testing Attendance 5-Pillar Zero-Trust, Attendance-Gated Tasks, 30-min PoPV Dwell Enforcement,
Client OTP Lockouts, Travel Mileage Anti-Fraud (>15%), and Admin Approval Workflows.
"""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest

from app.models.attendance import AttendanceRecord
from app.models.employee import Employee
from app.models.tenant import Office, Tenant
from app.models.task import Project, Task, TaskTimeEntry
from app.models.field_visit import ClientDestination, FieldVisitStop, ClientOtpVerification, FieldVisitProof
from app.models.travel import TravelLog, Vehicle
from app.schemas.attendance import (
    ClockInRequest,
    ClockInResponse,
    ClockOutRequest,
    FaceVerificationAudit,
    LocationAudit,
    NetworkAudit,
)
from app.schemas.kiosk import DynamicQRPayload
from app.schemas.task import StartTimerRequest, StopTimerRequest
from app.schemas.field_visit import CompleteVisitRequest, StopArriveRequest
from app.schemas.travel import EndTravelRequest, StartTravelRequest
from app.schemas.admin import ApproveReimbursementRequest, TenantPolicyUpdate
from app.services.attendance_service import AttendanceVerificationService
from app.services.task_service import TaskTrackingService
from app.services.field_visit_service import FieldVisitService
from app.services.travel_service import TravelTrackingService
from app.services.admin_service import AdminDashboardService
from app.services.qr_service import DynamicQRService


# ==============================================================================
# 1. ATTENDANCE ZERO-TRUST 5-PILLAR DEFENSES
# ==============================================================================

@pytest.mark.asyncio
async def test_device_mismatch_blocks_clockin():
    """Pillar 2: Reject attendance if smartphone hardware UUID differs from enrolled device."""
    db = AsyncMock()
    qr_service = AsyncMock()
    qr_service.consume_nonce.return_value = (True, None)

    service = AttendanceVerificationService(db=db, qr_service=qr_service)
    emp_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    # Employee enrolled with DEV-SECURE-1
    mock_emp = MagicMock(spec=Employee)
    mock_emp.id = emp_id
    mock_emp.tenant_id = tenant_id
    mock_emp.registered_device_id = "DEV-SECURE-1"
    
    mock_emp_res = MagicMock()
    mock_emp_res.scalar_one_or_none.return_value = mock_emp
    db.execute.return_value = mock_emp_res

    # Device in request is DEV-FRAUD-2
    req = ClockInRequest(
        device_id="DEV-FRAUD-2",
        qr_payload=DynamicQRPayload(t_id=str(tenant_id), o_id=str(uuid.uuid4()), nonce="a"*32, ts=1000, ttl=15, sig="b"*64),
        location=LocationAudit(latitude=28.4986, longitude=77.0878, accuracy_meters=5.0, is_mock=False),
        network_audit=NetworkAudit(wifi_bssid="3c:37:12:89:af:90"),
        face_verification=FaceVerificationAudit(liveness_passed=True, captured_embedding=[0.1]*128),
    )

    success, error_msg, response = await service.verify_and_clock_in(
        employee_id=emp_id, tenant_id=tenant_id, client_ip="127.0.0.1", request=req
    )

    assert success is False
    assert "DEVICE_MISMATCH" in error_msg
    assert response is None


@pytest.mark.asyncio
async def test_mock_gps_blocks_clockin():
    """Pillar 3: Mock location provider active on smartphone is immediately rejected."""
    db = AsyncMock()
    qr_service = AsyncMock()
    qr_service.consume_nonce.return_value = (True, None)

    service = AttendanceVerificationService(db=db, qr_service=qr_service)
    emp_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    mock_emp = MagicMock(spec=Employee)
    mock_emp.registered_device_id = "DEV-OK"
    mock_emp_res = MagicMock()
    mock_emp_res.scalar_one_or_none.return_value = mock_emp
    db.execute.return_value = mock_emp_res

    req = ClockInRequest(
        device_id="DEV-OK",
        qr_payload=DynamicQRPayload(t_id=str(tenant_id), o_id=str(uuid.uuid4()), nonce="a"*32, ts=1000, ttl=15, sig="b"*64),
        location=LocationAudit(latitude=28.4986, longitude=77.0878, accuracy_meters=5.0, is_mock=True),  # SPOOF!
        network_audit=NetworkAudit(wifi_bssid="3c:37:12:89:af:90"),
        face_verification=FaceVerificationAudit(liveness_passed=True, captured_embedding=[0.1]*128),
    )

    success, error_msg, response = await service.verify_and_clock_in(
        employee_id=emp_id, tenant_id=tenant_id, client_ip="127.0.0.1", request=req
    )

    assert success is False
    assert "SPOOF_DETECTED" in error_msg


@pytest.mark.asyncio
async def test_unauthorized_bssid_blocks_clockin():
    """Pillar 4: Wi-Fi BSSID not matching authorized office router list is rejected."""
    db = AsyncMock()
    qr_service = AsyncMock()
    qr_service.consume_nonce.return_value = (True, None)

    service = AttendanceVerificationService(db=db, qr_service=qr_service)
    emp_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    mock_emp = MagicMock(spec=Employee)
    mock_emp.registered_device_id = "DEV-OK"

    mock_office = MagicMock(spec=Office)
    mock_office.name = "HQ Cyber City"
    mock_office.allowed_bssid_list = ["3c:37:12:89:af:90"]  # Office router MAC

    mock_emp_res = MagicMock()
    mock_emp_res.scalar_one_or_none.return_value = mock_emp
    mock_off_res = MagicMock()
    mock_off_res.scalar_one_or_none.return_value = mock_office

    db.execute.side_effect = [mock_emp_res, mock_off_res]

    # Phone connected to rogue / home router
    req = ClockInRequest(
        device_id="DEV-OK",
        qr_payload=DynamicQRPayload(t_id=str(tenant_id), o_id=str(uuid.uuid4()), nonce="a"*32, ts=1000, ttl=15, sig="b"*64),
        location=LocationAudit(latitude=28.4986, longitude=77.0878, accuracy_meters=5.0, is_mock=False),
        network_audit=NetworkAudit(wifi_bssid="aa:bb:cc:dd:ee:ff"),
        face_verification=FaceVerificationAudit(liveness_passed=True, captured_embedding=[0.1]*128),
    )

    success, error_msg, response = await service.verify_and_clock_in(
        employee_id=emp_id, tenant_id=tenant_id, client_ip="127.0.0.1", request=req
    )

    assert success is False
    assert "NETWORK_MISMATCH" in error_msg


@pytest.mark.asyncio
async def test_face_similarity_below_threshold_blocks_clockin():
    """Pillar 5: Face verification below 0.82 cosine similarity threshold is rejected."""
    db = AsyncMock()
    qr_service = AsyncMock()
    qr_service.consume_nonce.return_value = (True, None)

    service = AttendanceVerificationService(db=db, qr_service=qr_service)
    emp_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    mock_emp = MagicMock(spec=Employee)
    mock_emp.registered_device_id = "DEV-OK"
    mock_emp.face_embedding_vector = [1.0, 0.0, 0.0, 0.0]  # Baseline

    mock_office = MagicMock(spec=Office)
    mock_office.name = "HQ Cyber City"
    mock_office.allowed_bssid_list = ["3c:37:12:89:af:90"]

    db.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: mock_emp),
        MagicMock(scalar_one_or_none=lambda: mock_office),
    ]

    # Captured embedding is orthogonal (cosine similarity = 0.0 < 0.82)
    req = ClockInRequest(
        device_id="DEV-OK",
        qr_payload=DynamicQRPayload(t_id=str(tenant_id), o_id=str(uuid.uuid4()), nonce="a"*32, ts=1000, ttl=15, sig="b"*64),
        location=LocationAudit(latitude=28.4986, longitude=77.0878, accuracy_meters=5.0, is_mock=False),
        network_audit=NetworkAudit(wifi_bssid="3c:37:12:89:af:90"),
        face_verification=FaceVerificationAudit(liveness_passed=True, captured_embedding=[0.0, 1.0, 0.0, 0.0]),
    )

    success, error_msg, response = await service.verify_and_clock_in(
        employee_id=emp_id, tenant_id=tenant_id, client_ip="127.0.0.1", request=req
    )

    assert success is False
    assert "FACE_MISMATCH" in error_msg


# ==============================================================================
# 2. ATTENDANCE-GATED TASK TRACKING
# ==============================================================================

@pytest.mark.asyncio
async def test_task_timer_requires_active_attendance():
    """Task timer CANNOT start if employee is not physically clocked in."""
    db = AsyncMock()
    service = TaskTrackingService(db=db)
    tenant_id = uuid.uuid4()
    emp_id = uuid.uuid4()

    # DB query returns no active attendance record
    mock_att_res = MagicMock()
    mock_att_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_att_res

    req = StartTimerRequest(task_id=uuid.uuid4(), notes="Trying to start without clocking in")
    success, error_msg, response = await service.start_task_timer(tenant_id, emp_id, req)

    assert success is False
    assert "ATTENDANCE_REQUIRED" in error_msg
    assert response is None


@pytest.mark.asyncio
async def test_task_timer_auto_stops_previous_timer():
    """Starting task B when task A is already running automatically stops task A."""
    db = AsyncMock()
    service = TaskTrackingService(db=db)
    tenant_id = uuid.uuid4()
    emp_id = uuid.uuid4()

    mock_att = MagicMock(spec=AttendanceRecord)
    mock_att.id = uuid.uuid4()

    # Active running task A
    active_task_a = MagicMock(spec=TaskTimeEntry)
    active_task_a.end_time = None

    mock_att_res = MagicMock(scalar_one_or_none=lambda: mock_att)
    mock_running_res = MagicMock(scalars=lambda: MagicMock(all=lambda: [active_task_a]))
    mock_task_res = MagicMock(scalar_one_or_none=lambda: MagicMock(status="TODO"))

    db.execute.side_effect = [mock_att_res, mock_running_res, mock_task_res]

    req = StartTimerRequest(task_id=uuid.uuid4(), notes="Switching to Task B")
    success, error_msg, response = await service.start_task_timer(tenant_id, emp_id, req)

    assert success is True
    # Confirm task A was auto-stopped
    assert active_task_a.end_time is not None


# ==============================================================================
# 3. VERIFIABLE FIELD VISIT (30-MIN DWELL & CLIENT OTP)
# ==============================================================================

@pytest.mark.asyncio
async def test_field_visit_dwell_time_not_met_blocks_completion():
    """Anti-Drive-By: Field visit cannot be marked complete if dwell time < 30 mins."""
    db = AsyncMock()
    service = FieldVisitService(db=db)
    tenant_id = uuid.uuid4()
    stop_id = uuid.uuid4()

    mock_destination = MagicMock(spec=ClientDestination)
    mock_destination.name = "City Hospital"
    mock_destination.min_dwell_minutes = 30

    mock_stop = MagicMock(spec=FieldVisitStop)
    mock_stop.status = "ARRIVED"
    # Arrived only 10 minutes ago
    mock_stop.actual_arrival_time = datetime.now(timezone.utc) - timedelta(minutes=10)

    mock_res = MagicMock()
    mock_res.first.return_value = (mock_stop, mock_destination)
    db.execute.return_value = mock_res

    req = CompleteVisitRequest(
        otp_id=uuid.uuid4(),
        otp_code="1234",
        photo_file_url="https://s3.example.com/proof.jpg",
        watermark_hash="hash-abc-123",
        latitude=28.5355,
        longitude=77.3910,
    )

    success, error_msg, response = await service.complete_field_visit(tenant_id, stop_id, req)

    assert success is False
    assert "DWELL_TIME_NOT_MET" in error_msg
    assert "20 mins remaining" in error_msg


@pytest.mark.asyncio
async def test_field_visit_otp_wrong_code_increments_attempts():
    """Incorrect OTP decrements remaining attempts and returns count."""
    db = AsyncMock()
    service = FieldVisitService(db=db)
    tenant_id = uuid.uuid4()
    stop_id = uuid.uuid4()

    mock_destination = MagicMock(spec=ClientDestination)
    mock_destination.min_dwell_minutes = 30

    mock_stop = MagicMock(spec=FieldVisitStop)
    mock_stop.status = "ARRIVED"
    mock_stop.actual_arrival_time = datetime.now(timezone.utc) - timedelta(minutes=35)  # Dwell satisfied

    mock_otp = MagicMock(spec=ClientOtpVerification)
    mock_otp.status = "SENT"
    mock_otp.otp_code = "9999"  # Actual code
    mock_otp.attempts = 0
    mock_otp.max_attempts = 3
    mock_otp.expires_at = datetime.now(timezone.utc) + timedelta(minutes=4)

    mock_stop_res = MagicMock(first=lambda: (mock_stop, mock_destination))
    mock_otp_res = MagicMock(scalar_one_or_none=lambda: mock_otp)
    db.execute.side_effect = [mock_stop_res, mock_otp_res]

    # Submit wrong code "1111"
    req = CompleteVisitRequest(
        otp_id=uuid.uuid4(),
        otp_code="1111",
        photo_file_url="https://s3.example.com/proof.jpg",
        watermark_hash="hash-abc",
        latitude=28.5355,
        longitude=77.3910,
    )

    success, error_msg, response = await service.complete_field_visit(tenant_id, stop_id, req)

    assert success is False
    assert "OTP_INVALID" in error_msg
    assert mock_otp.attempts == 1
    assert "2 attempts remaining" in error_msg


# ==============================================================================
# 4. TRAVEL MILEAGE & 15% ANTI-FRAUD ENGINE
# ==============================================================================

@pytest.mark.asyncio
async def test_travel_odometer_fraud_discrepancy_alert():
    """Odometer difference exceeding GPS breadcrumb distance by >15% triggers fraud flag."""
    db = AsyncMock()
    service = TravelTrackingService(db=db)
    tenant_id = uuid.uuid4()
    emp_id = uuid.uuid4()

    mock_log = MagicMock(spec=TravelLog)
    mock_log.id = uuid.uuid4()
    mock_log.status = "ACTIVE"
    mock_log.transport_mode = "PERSONAL_CAR"
    mock_log.reimbursement_rate_per_km = 8.00
    mock_log.odometer_start_km = 10000.0
    mock_log.gps_total_distance_km = 40.0  # Verified GPS distance = 40 km

    mock_res = MagicMock(scalar_one_or_none=lambda: mock_log)
    db.execute.return_value = mock_res

    # End shift with odometer = 10070.0 (Difference = 70 km, vs GPS 40 km -> 42.8% discrepancy!)
    req = EndTravelRequest(
        travel_log_id=mock_log.id,
        odometer_end_km=10070.0,
        odometer_end_photo_url="https://s3.example.com/odo_end.jpg",
    )

    success, error_msg, response = await service.end_travel_shift(tenant_id, emp_id, req)

    assert success is True
    assert response.is_discrepancy_flagged is True
    assert response.discrepancy_pct > 15.0
    assert "Warning" in response.message
    # Reimbursement must cap at verified GPS distance (40 km * 8 = 320)
    assert response.reimbursement_amount == 320.0


# ==============================================================================
# 5. EMPLOYER ADMIN APPROVAL & POLICY WORKFLOW
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_reimbursement_approval_and_rejection():
    """Admin can approve or reject travel claims and adjust approved amounts."""
    db = AsyncMock()
    service = AdminDashboardService(db=db)
    tenant_id = uuid.uuid4()
    claim_id = uuid.uuid4()

    mock_log = MagicMock(spec=TravelLog)
    mock_log.id = claim_id
    mock_log.reimbursement_status = "PENDING"
    mock_log.reimbursement_amount = 500.0

    mock_res = MagicMock(scalar_one_or_none=lambda: mock_log)
    db.execute.return_value = mock_res

    # Approve with adjusted amount of 450.0
    req_approve = ApproveReimbursementRequest(action="APPROVE", approved_amount=450.0)
    success, err = await service.update_reimbursement_status(tenant_id, claim_id, req_approve)

    assert success is True
    assert mock_log.reimbursement_status == "APPROVED"
    assert mock_log.reimbursement_amount == 450.0

    # Reject
    req_reject = ApproveReimbursementRequest(action="REJECT")
    success, err = await service.update_reimbursement_status(tenant_id, claim_id, req_reject)
    assert success is True
    assert mock_log.reimbursement_status == "REJECTED"


@pytest.mark.asyncio
async def test_admin_policy_update():
    """Admin can configure default dwell minutes and travel rates."""
    db = AsyncMock()
    service = AdminDashboardService(db=db)
    tenant_id = uuid.uuid4()

    mock_tenant = MagicMock(spec=Tenant)
    mock_tenant.configuration = {
        "field_visit_default_dwell_minutes": 30,
        "travel_reimbursement_rates": {"PERSONAL_CAR": 8.00, "TWO_WHEELER": 4.00},
    }

    mock_res = MagicMock(scalar_one_or_none=lambda: mock_tenant)
    db.execute.return_value = mock_res

    update_req = TenantPolicyUpdate(
        field_visit_default_dwell_minutes=45,
        car_reimbursement_rate=10.00,
        bike_reimbursement_rate=5.00,
    )

    success, new_cfg = await service.update_tenant_policy(tenant_id, update_req)

    assert success is True
    assert new_cfg["field_visit_default_dwell_minutes"] == 45
    assert new_cfg["travel_reimbursement_rates"]["PERSONAL_CAR"] == 10.00
    assert new_cfg["travel_reimbursement_rates"]["TWO_WHEELER"] == 5.00
