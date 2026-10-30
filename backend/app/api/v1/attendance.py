"""Attendance API endpoints for mobile client clock-in and clock-out."""

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.redis import get_redis_client
from app.models.attendance import AttendanceRecord
from app.schemas.attendance import ClockInRequest, ClockInResponse, ClockOutRequest, ClockOutResponse
from app.services.attendance_service import AttendanceVerificationService
from app.services.qr_service import DynamicQRService

router = APIRouter(prefix="/attendance", tags=["Attendance Verification"])


async def get_attendance_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AttendanceVerificationService:
    """Dependency supplying initialized AttendanceVerificationService."""
    try:
        redis_client = await get_redis_client()
    except Exception:
        redis_client = None
    qr_service = DynamicQRService(redis_client=redis_client)
    return AttendanceVerificationService(db=db, qr_service=qr_service)


@router.post("/clock-in", response_model=ClockInResponse)
async def clock_in(
    request: ClockInRequest,
    http_request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    attendance_service: Annotated[AttendanceVerificationService, Depends(get_attendance_service)],
):
    """
    Submits zero-trust physical attendance verification payload.
    Validates Dynamic QR, Hardware Device Binding, Wi-Fi BSSID, and On-Device Facial Liveness.
    """
    employee_id = uuid.UUID(current_user["sub"])
    tenant_id = uuid.UUID(current_user["tenant_id"])
    client_ip = http_request.client.host if http_request.client else "127.0.0.1"

    success, error_msg, response = await attendance_service.verify_and_clock_in(
        employee_id=employee_id,
        tenant_id=tenant_id,
        client_ip=client_ip,
        request=request,
    )

    if not success:
        if "QR_VERIFICATION_FAILED" in str(error_msg):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
        elif "DEVICE_MISMATCH" in str(error_msg) or "NETWORK_MISMATCH" in str(error_msg):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)
        elif "SPOOF_DETECTED" in str(error_msg) or "LIVENESS_FAILED" in str(error_msg) or "FACE_MISMATCH" in str(error_msg):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error_msg)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    return response


@router.post("/clock-out", response_model=ClockOutResponse)
async def clock_out(
    request: ClockOutRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    attendance_service: Annotated[AttendanceVerificationService, Depends(get_attendance_service)],
):
    """
    Submits clock-out and automatically closes any open task timers.
    """
    employee_id = uuid.UUID(current_user["sub"])
    tenant_id = uuid.UUID(current_user["tenant_id"])

    success, error_msg, response = await attendance_service.clock_out(
        employee_id=employee_id,
        tenant_id=tenant_id,
        request=request,
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    return response
