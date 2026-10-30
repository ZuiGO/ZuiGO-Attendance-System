"""Pydantic schemas for Vehicle Registry, Travel Logs, and Mileage Tracking."""

from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field


class VehicleCreate(BaseModel):
    ownership_type: str = Field(default="COMPANY")  # COMPANY, PERSONAL
    vehicle_type: str = Field(..., description="CAR, TWO_WHEELER, VAN, TRUCK")
    registration_number: str = Field(..., max_length=30)
    make_model: Optional[str] = None
    fuel_type: str = Field(default="PETROL")
    assigned_employee_id: Optional[uuid.UUID] = None


class VehicleResponse(BaseModel):
    id: str
    tenant_id: str
    ownership_type: str
    vehicle_type: str
    registration_number: str
    make_model: Optional[str] = None
    fuel_type: str
    assigned_employee_id: Optional[str] = None
    is_active: bool


class StartTravelRequest(BaseModel):
    itinerary_id: Optional[uuid.UUID] = None
    transport_mode: str = Field(..., description="COMPANY_CAR, PERSONAL_CAR, TWO_WHEELER, CAB, PUBLIC_TRANSPORT, WALKING")
    vehicle_id: Optional[uuid.UUID] = None
    odometer_start_km: Optional[float] = None
    odometer_start_photo_url: Optional[str] = None


class StartTravelResponse(BaseModel):
    travel_log_id: str
    transport_mode: str
    shift_start_time: str
    reimbursement_rate_per_km: float
    status: str


class EndTravelRequest(BaseModel):
    travel_log_id: uuid.UUID
    odometer_end_km: Optional[float] = None
    odometer_end_photo_url: Optional[str] = None


class EndTravelResponse(BaseModel):
    travel_log_id: str
    transport_mode: str
    odometer_distance_km: Optional[float] = None
    gps_computed_distance_km: float
    discrepancy_pct: Optional[float] = None
    is_discrepancy_flagged: bool
    reimbursement_rate_per_km: float
    reimbursement_amount: float
    reimbursement_status: str
    status: str
    message: str


class TravelReceiptUploadRequest(BaseModel):
    travel_log_id: uuid.UUID
    receipt_type: str = Field(..., description="CAB_RECEIPT, BUS_TICKET, METRO_PASS, TOLL_RECEIPT, FUEL_RECEIPT")
    amount: float = Field(..., gt=0.0)
    currency: str = Field(default="INR")
    receipt_photo_url: str
    notes: Optional[str] = None


class TravelReceiptResponse(BaseModel):
    receipt_id: str
    travel_log_id: str
    receipt_type: str
    amount: float
    currency: str
    created_at: str
