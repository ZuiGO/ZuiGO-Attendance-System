"""Multi-Factor Physical Presence Attendance Verification (MFPV) Service."""

from datetime import date, datetime, timezone
import math
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRecord
from app.models.employee import Employee
from app.models.tenant import Office
from app.models.task import TaskTimeEntry
from app.schemas.attendance import ClockInRequest, ClockInResponse, ClockOutRequest, ClockOutResponse
from app.services.qr_service import DynamicQRService


def calculate_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two N-dimensional facial embeddings."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def calculate_haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two geographic coordinates in meters."""
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class AttendanceVerificationService:
    """Service executing the Zero-Trust Multi-Factor Presence Verification Pipeline."""

    def __init__(self, db: AsyncSession, qr_service: DynamicQRService):
        self.db = db
        self.qr_service = qr_service

    async def verify_and_clock_in(
        self,
        employee_id: uuid.UUID,
        tenant_id: uuid.UUID,
        client_ip: str,
        request: ClockInRequest,
    ) -> Tuple[bool, Optional[str], Optional[ClockInResponse]]:
        """
        Executes the 5 zero-trust verification pillars:
          1. Dynamic Rotating QR Nonce Consumption (Anti-Screenshot/Proxy)
          2. 1:1 Hardware Device Binding
          3. OS Mock Location Detection
          4. Wi-Fi BSSID Network Geofence
          5. Facial Liveness & Cosine Similarity Match
        """
        # Pillar 1: Dynamic QR Code Verification & Atomic Nonce Consumption
        qr = request.qr_payload
        is_qr_valid, qr_error = await self.qr_service.consume_nonce(
            tenant_id=qr.t_id,
            office_id=qr.o_id,
            nonce=qr.nonce,
            timestamp=qr.ts,
            signature=qr.sig,
        )
        if not is_qr_valid:
            return False, f"QR_VERIFICATION_FAILED: {qr_error}", None

        # Fetch employee record
        emp_stmt = select(Employee).where(Employee.id == employee_id, Employee.tenant_id == tenant_id)
        emp_res = await self.db.execute(emp_stmt)
        employee = emp_res.scalar_one_or_none()
        if not employee:
            return False, "EMPLOYEE_NOT_FOUND", None

        # Pillar 2: 1:1 Hardware Device Binding
        if employee.registered_device_id and employee.registered_device_id != request.device_id:
            return False, f"DEVICE_MISMATCH: Attendance must be recorded from registered device ({employee.registered_device_id})", None

        # Pillar 3: Mock Location Detection
        if request.location.is_mock:
            return False, "SPOOF_DETECTED: Mock location provider active on device", None

        # Fetch office details
        office_id_uuid = uuid.UUID(qr.o_id)
        office_stmt = select(Office).where(Office.id == office_id_uuid, Office.tenant_id == tenant_id)
        office_res = await self.db.execute(office_stmt)
        office = office_res.scalar_one_or_none()
        if not office:
            return False, "OFFICE_NOT_FOUND", None

        # Pillar 4: Wi-Fi BSSID Validation (Network Geofencing)
        if office.allowed_bssid_list:
            client_bssid = request.network_audit.wifi_bssid.lower().strip()
            allowed_bssids = [b.lower().strip() for b in office.allowed_bssid_list]
            if client_bssid not in allowed_bssids:
                return False, f"NETWORK_MISMATCH: Connected BSSID ({client_bssid}) not authorized for {office.name}", None

        # Pillar 5: Facial Liveness & AI Embedding Match
        if not request.face_verification.liveness_passed:
            return False, "LIVENESS_FAILED: Facial scan failed 3D liveness detection", None

        similarity_score = 1.0
        if employee.face_embedding_vector:
            similarity_score = calculate_cosine_similarity(
                employee.face_embedding_vector,
                request.face_verification.captured_embedding,
            )
            # Threshold: 0.82 cosine similarity
            if similarity_score < 0.82:
                return False, f"FACE_MISMATCH: Facial similarity {similarity_score:.3f} below required 0.82 threshold", None

        # Check if already clocked in today
        today = date.today()
        existing_stmt = select(AttendanceRecord).where(
            AttendanceRecord.tenant_id == tenant_id,
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.date == today,
        )
        existing_res = await self.db.execute(existing_stmt)
        existing_record = existing_res.scalar_one_or_none()
        if existing_record and existing_record.clock_out is None:
            return False, "ALREADY_CLOCKED_IN: Active attendance session already in progress for today", None

        # Register Attendance Record
        now = datetime.now(timezone.utc)
        point_wkt = f"SRID=4326;POINT({request.location.longitude} {request.location.latitude})"

        record = AttendanceRecord(
            tenant_id=tenant_id,
            employee_id=employee_id,
            office_id=office.id,
            date=today,
            clock_in=now,
            clock_in_verification_method="DYNAMIC_QR_FACE_WIFI",
            clock_in_location=point_wkt,
            clock_in_bssid=request.network_audit.wifi_bssid,
            clock_in_client_ip=client_ip,
            clock_in_device_id=request.device_id,
            clock_in_face_similarity_score=similarity_score,
            status="PRESENT",
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        response = ClockInResponse(
            attendance_id=str(record.id),
            status="PRESENT",
            clock_in_time=now.isoformat(),
            office_name=office.name,
            similarity_score=round(similarity_score, 4),
            message=f"Physical presence verified at {office.name}. Clocked in successfully.",
        )
        return True, None, response

    async def clock_out(
        self,
        employee_id: uuid.UUID,
        tenant_id: uuid.UUID,
        request: ClockOutRequest,
    ) -> Tuple[bool, Optional[str], Optional[ClockOutResponse]]:
        """Handles clock-out and automatically closes any running task timers."""
        record_id = uuid.UUID(request.attendance_id)
        stmt = select(AttendanceRecord).where(
            AttendanceRecord.id == record_id,
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.tenant_id == tenant_id,
        )
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            return False, "ATTENDANCE_RECORD_NOT_FOUND", None

        if record.clock_out is not None:
            return False, "ALREADY_CLOCKED_OUT", None

        now = datetime.now(timezone.utc)
        record.clock_out = now
        point_wkt = f"SRID=4326;POINT({request.location.longitude} {request.location.latitude})"
        record.clock_out_location = point_wkt
        record.clock_out_verification_method = "MOBILE_APP"

        # Calculate total shift duration in hours
        duration_seconds = (now - record.clock_in).total_seconds()
        shift_hours = round(duration_seconds / 3600.0, 2)

        # Auto-stop any active running task timers for this employee
        active_tasks_stmt = select(TaskTimeEntry).where(
            TaskTimeEntry.employee_id == employee_id,
            TaskTimeEntry.tenant_id == tenant_id,
            TaskTimeEntry.end_time.is_(None),
        )
        active_tasks_res = await self.db.execute(active_tasks_stmt)
        active_entries = active_tasks_res.scalars().all()
        stopped_count = 0
        for entry in active_entries:
            entry.end_time = now
            stopped_count += 1

        await self.db.commit()

        response = ClockOutResponse(
            attendance_id=str(record.id),
            clock_out_time=now.isoformat(),
            total_shift_hours=shift_hours,
            active_tasks_stopped=stopped_count,
            message="Clock-out confirmed. Active task timers automatically closed.",
        )
        return True, None, response
