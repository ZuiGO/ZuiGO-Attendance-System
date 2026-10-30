"""Field-Visit (PoPV), 30-min Dwell Time, and Client OTP API endpoints."""

from typing import Annotated, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.field_visit import (
    ClientDestinationCreate,
    ClientDestinationResponse,
    CompleteVisitRequest,
    CompleteVisitResponse,
    RequestOtpRequest,
    RequestOtpResponse,
    StopArriveRequest,
    StopArriveResponse,
)
from app.services.field_visit_service import FieldVisitService

router = APIRouter(prefix="/field", tags=["Field Visits & Client OTP (PoPV)"])


def get_field_service(db: Annotated[AsyncSession, Depends(get_db)]) -> FieldVisitService:
    return FieldVisitService(db=db)


@router.post("/destinations", response_model=ClientDestinationResponse)
async def create_destination(
    data: ClientDestinationCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    field_service: Annotated[FieldVisitService, Depends(get_field_service)],
):
    """Registers a hospital, dealer, distributor, or client destination with PostGIS coordinates."""
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await field_service.create_destination(tenant_id=tenant_id, data=data)


@router.post("/visits/{stop_id}/arrive", response_model=StopArriveResponse)
async def arrive_at_field_stop(
    stop_id: uuid.UUID,
    data: StopArriveRequest,
    dest_lat: Annotated[float, Query(description="Target destination latitude")],
    dest_lon: Annotated[float, Query(description="Target destination longitude")],
    current_user: Annotated[dict, Depends(get_current_user)],
    field_service: Annotated[FieldVisitService, Depends(get_field_service)],
):
    """
    Geofence Arrival Check:
      - Validates physical proximity to destination (< 75m).
      - Rejects mock GPS / spoofing apps.
      - Starts the 30-minute dwell timer.
    """
    tenant_id = uuid.UUID(current_user["tenant_id"])
    employee_id = uuid.UUID(current_user["sub"])

    success, error_msg, response = await field_service.arrive_at_stop(
        tenant_id=tenant_id,
        employee_id=employee_id,
        stop_id=stop_id,
        data=data,
        dest_lat=dest_lat,
        dest_lon=dest_lon,
    )
    if not success:
        if "OUTSIDE_GEOFENCE" in str(error_msg):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)
        elif "SPOOF_DETECTED" in str(error_msg):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    return response


@router.post("/visits/{stop_id}/request-otp", response_model=RequestOtpResponse)
async def request_client_otp(
    stop_id: uuid.UUID,
    data: RequestOtpRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    field_service: Annotated[FieldVisitService, Depends(get_field_service)],
):
    """Dispatches a 4-digit verification code to the client contact via SMS or WhatsApp."""
    tenant_id = uuid.UUID(current_user["tenant_id"])

    success, error_msg, response = await field_service.request_client_otp(
        tenant_id=tenant_id,
        stop_id=stop_id,
        preferred_channel=data.channel,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    return response


@router.post("/visits/{stop_id}/complete", response_model=CompleteVisitResponse)
async def complete_field_visit(
    stop_id: uuid.UUID,
    data: CompleteVisitRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    field_service: Annotated[FieldVisitService, Depends(get_field_service)],
):
    """
    Finalizes field visit by enforcing:
      1. 30-min minimum dwell time (Anti-Drive-By).
      2. Validated Client SMS/WhatsApp OTP.
      3. Live camera photo proof with cryptographic watermark.
    """
    tenant_id = uuid.UUID(current_user["tenant_id"])

    success, error_msg, response = await field_service.complete_field_visit(
        tenant_id=tenant_id,
        stop_id=stop_id,
        data=data,
    )
    if not success:
        if "DWELL_TIME_NOT_MET" in str(error_msg) or "OTP_INVALID" in str(error_msg) or "OTP_EXPIRED" in str(error_msg):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
        elif "OTP_MAX_ATTEMPTS" in str(error_msg):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    return response
