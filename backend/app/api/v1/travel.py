"""Transport Mode, Vehicle Registry, Mileage Tracking, and Reimbursement API endpoints."""

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.travel import (
    EndTravelRequest,
    EndTravelResponse,
    StartTravelRequest,
    StartTravelResponse,
    VehicleCreate,
    VehicleResponse,
)
from app.services.travel_service import TravelTrackingService

router = APIRouter(prefix="/travel", tags=["Transport Mode, Mileage & Reimbursement"])


def get_travel_service(db: Annotated[AsyncSession, Depends(get_db)]) -> TravelTrackingService:
    return TravelTrackingService(db=db)


@router.post("/vehicles", response_model=VehicleResponse)
async def register_vehicle(
    data: VehicleCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    travel_service: Annotated[TravelTrackingService, Depends(get_travel_service)],
):
    """Registers a company fleet vehicle or employee personal vehicle."""
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await travel_service.register_vehicle(tenant_id=tenant_id, data=data)


@router.post("/start", response_model=StartTravelResponse)
async def start_travel_shift(
    data: StartTravelRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    travel_service: Annotated[TravelTrackingService, Depends(get_travel_service)],
):
    """
    Begins field travel:
      - Records transport mode (Personal Car, Two-Wheeler, Cab, etc.)
      - Records starting odometer reading and photo.
      - Sets per-km reimbursement rate.
    """
    tenant_id = uuid.UUID(current_user["tenant_id"])
    employee_id = uuid.UUID(current_user["sub"])
    return await travel_service.start_travel_shift(
        tenant_id=tenant_id,
        employee_id=employee_id,
        data=data,
    )


@router.post("/end", response_model=EndTravelResponse)
async def end_travel_shift(
    data: EndTravelRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    travel_service: Annotated[TravelTrackingService, Depends(get_travel_service)],
):
    """
    Ends field travel:
      - Validates ending odometer reading and photo.
      - Cross-checks odometer distance against GPS breadcrumb polyline.
      - Auto-flags discrepancies exceeding 15% (fraud alert).
      - Computes verified mileage reimbursement.
    """
    tenant_id = uuid.UUID(current_user["tenant_id"])
    employee_id = uuid.UUID(current_user["sub"])

    success, error_msg, response = await travel_service.end_travel_shift(
        tenant_id=tenant_id,
        employee_id=employee_id,
        data=data,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    return response
