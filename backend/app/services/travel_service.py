"""Travel, Vehicle Registry, Mileage Tracking, and Reimbursement Engine."""

from datetime import datetime, timezone
import math
from typing import Optional, Tuple
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.tenant import Tenant
from app.models.travel import TravelExpenseReceipt, TravelLeg, TravelLog, Vehicle
from app.schemas.travel import (
    EndTravelRequest,
    EndTravelResponse,
    StartTravelRequest,
    StartTravelResponse,
    TravelReceiptResponse,
    TravelReceiptUploadRequest,
    VehicleCreate,
    VehicleResponse,
)


def calculate_mileage_reimbursement(
    transport_mode: str,
    distance_km: float,
    rate_per_km: float,
) -> float:
    """Calculates reimbursement amount based on transport mode and distance."""
    if transport_mode in ("COMPANY_CAR", "WALKING"):
        return 0.0
    return round(distance_km * rate_per_km, 2)


def check_odometer_discrepancy(
    odometer_km: float,
    gps_km: float,
    threshold_pct: float = 15.0,
) -> Tuple[float, bool]:
    """
    Computes discrepancy percentage between odometer reading and GPS breadcrumbs.
    Returns (discrepancy_pct, is_flagged).
    """
    if odometer_km <= 0.0:
        return 0.0, False

    diff = abs(odometer_km - gps_km)
    discrepancy_pct = (diff / odometer_km) * 100.0
    is_flagged = discrepancy_pct > threshold_pct
    return round(discrepancy_pct, 2), is_flagged


class TravelTrackingService:
    """Service tracking transport mode, vehicle mileage, and travel expenses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_vehicle(self, tenant_id: uuid.UUID, data: VehicleCreate) -> VehicleResponse:
        """Enrolls a company fleet vehicle or employee personal vehicle."""
        vehicle = Vehicle(
            tenant_id=tenant_id,
            ownership_type=data.ownership_type,
            vehicle_type=data.vehicle_type,
            registration_number=data.registration_number.upper().strip(),
            make_model=data.make_model,
            fuel_type=data.fuel_type,
            assigned_employee_id=data.assigned_employee_id,
        )
        self.db.add(vehicle)
        await self.db.commit()
        await self.db.refresh(vehicle)

        return VehicleResponse(
            id=str(vehicle.id),
            tenant_id=str(vehicle.tenant_id),
            ownership_type=vehicle.ownership_type,
            vehicle_type=vehicle.vehicle_type,
            registration_number=vehicle.registration_number,
            make_model=vehicle.make_model,
            fuel_type=vehicle.fuel_type,
            assigned_employee_id=str(vehicle.assigned_employee_id) if vehicle.assigned_employee_id else None,
            is_active=vehicle.is_active,
        )

    async def start_travel_shift(
        self,
        tenant_id: uuid.UUID,
        employee_id: uuid.UUID,
        data: StartTravelRequest,
    ) -> StartTravelResponse:
        """Starts a field travel shift with declared transport mode and odometer baseline."""
        rate = 0.0
        if data.transport_mode == "PERSONAL_CAR":
            rate = float(settings.REIMBURSEMENT_RATES.get("PERSONAL_CAR", 8.00))
        elif data.transport_mode == "TWO_WHEELER":
            rate = float(settings.REIMBURSEMENT_RATES.get("TWO_WHEELER", 4.00))

        now = datetime.now(timezone.utc)
        travel_log = TravelLog(
            tenant_id=tenant_id,
            employee_id=employee_id,
            itinerary_id=data.itinerary_id,
            vehicle_id=data.vehicle_id,
            transport_mode=data.transport_mode,
            shift_start_time=now,
            odometer_start_km=data.odometer_start_km,
            odometer_start_photo_url=data.odometer_start_photo_url,
            reimbursement_rate_per_km=rate,
            status="ACTIVE",
        )
        self.db.add(travel_log)
        await self.db.commit()
        await self.db.refresh(travel_log)

        return StartTravelResponse(
            travel_log_id=str(travel_log.id),
            transport_mode=travel_log.transport_mode,
            shift_start_time=now.isoformat(),
            reimbursement_rate_per_km=rate,
            status="ACTIVE",
        )

    async def end_travel_shift(
        self,
        tenant_id: uuid.UUID,
        employee_id: uuid.UUID,
        data: EndTravelRequest,
    ) -> Tuple[bool, Optional[str], Optional[EndTravelResponse]]:
        """
        Ends travel shift: validates odometer photos, compares with GPS distance, and computes reimbursement.
        """
        stmt = select(TravelLog).where(
            TravelLog.id == data.travel_log_id,
            TravelLog.employee_id == employee_id,
            TravelLog.tenant_id == tenant_id,
        )
        res = await self.db.execute(stmt)
        log = res.scalar_one_or_none()
        if not log:
            return False, "TRAVEL_LOG_NOT_FOUND", None

        if log.status == "COMPLETED":
            return False, "TRAVEL_LOG_ALREADY_COMPLETED", None

        now = datetime.now(timezone.utc)
        log.shift_end_time = now
        log.odometer_end_km = data.odometer_end_km
        log.odometer_end_photo_url = data.odometer_end_photo_url

        odometer_dist = 0.0
        if log.odometer_start_km is not None and log.odometer_end_km is not None:
            odometer_dist = float(log.odometer_end_km) - float(log.odometer_start_km)

        gps_dist = float(log.gps_total_distance_km or 0.0)
        # Check discrepancy
        discrepancy_pct, is_flagged = check_odometer_discrepancy(
            odometer_km=odometer_dist,
            gps_km=gps_dist,
            threshold_pct=settings.ODOMETER_DISCREPANCY_THRESHOLD_PCT,
        )

        log.distance_discrepancy_pct = discrepancy_pct
        log.is_discrepancy_flagged = is_flagged

        # Compute reimbursement based on verified GPS distance (or odometer distance if lower)
        effective_dist = min(odometer_dist, gps_dist) if odometer_dist > 0.0 and gps_dist > 0.0 else (gps_dist or odometer_dist)
        reimbursement = calculate_mileage_reimbursement(
            transport_mode=log.transport_mode,
            distance_km=effective_dist,
            rate_per_km=float(log.reimbursement_rate_per_km),
        )
        log.reimbursement_amount = reimbursement
        log.status = "COMPLETED"

        await self.db.commit()

        msg = "Travel completed."
        if is_flagged:
            msg += f" Warning: {discrepancy_pct}% discrepancy flagged between odometer ({odometer_dist}km) and GPS ({gps_dist}km)."

        response = EndTravelResponse(
            travel_log_id=str(log.id),
            transport_mode=log.transport_mode,
            odometer_distance_km=round(odometer_dist, 2) if odometer_dist > 0 else None,
            gps_computed_distance_km=round(gps_dist, 2),
            discrepancy_pct=discrepancy_pct,
            is_discrepancy_flagged=is_flagged,
            reimbursement_rate_per_km=float(log.reimbursement_rate_per_km),
            reimbursement_amount=reimbursement,
            reimbursement_status="PENDING",
            status="COMPLETED",
            message=msg,
        )
        return True, None, response
