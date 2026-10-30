"""Pydantic schemas for Verifiable Field-Visits (PoPV), 30-min Dwell Time, and Client OTP."""

from datetime import date as date_type, datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field


class ClientDestinationCreate(BaseModel):
    name: str = Field(..., max_length=255)
    client_type: str = Field(default="CUSTOMER")  # HOSPITAL, DEALER, DISTRIBUTOR, CUSTOMER
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    otp_channel: str = Field(default="SMS")  # SMS, WHATSAPP, BOTH
    address: Optional[str] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    geofence_radius_meters: int = Field(default=75)
    min_dwell_minutes: int = Field(default=30)  # Default 30 minutes minimum stay


class ClientDestinationResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    client_type: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    otp_channel: str
    address: Optional[str] = None
    geofence_radius_meters: int
    min_dwell_minutes: int
    is_active: bool


class FieldItineraryCreate(BaseModel):
    employee_id: uuid.UUID
    title: str = Field(..., max_length=200)
    itinerary_date: date_type = Field(default_factory=date_type.today)
    destination_ids: List[uuid.UUID] = Field(..., min_length=1)
    notes: Optional[str] = None


class StopArriveRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    accuracy_meters: Optional[float] = None
    is_mock: bool = Field(default=False)


class StopArriveResponse(BaseModel):
    stop_id: str
    status: str
    actual_arrival_time: str
    distance_from_target_meters: float
    min_dwell_minutes: int
    dwell_timer_ends_at: str
    message: str


class RequestOtpRequest(BaseModel):
    channel: Optional[str] = None  # None for default, or 'SMS' / 'WHATSAPP'


class RequestOtpResponse(BaseModel):
    otp_id: str
    recipient_phone_masked: str
    channel: str
    expires_in_seconds: int
    max_attempts: int
    message: str


class CompleteVisitRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    is_mock: bool = Field(default=False)
    
    # In-App Live Camera Photo Proof
    photo_file_url: str = Field(..., description="Uploaded camera snapshot URL")
    watermark_hash: str = Field(..., description="Cryptographic watermark signature")
    
    # Client Counter-Verification (SMS/WhatsApp OTP)
    otp_id: uuid.UUID
    otp_code: str = Field(..., min_length=4, max_length=6)
    
    meeting_notes: Optional[str] = None


class CompleteVisitResponse(BaseModel):
    stop_id: str
    status: str
    dwell_time_seconds: int
    dwell_time_formatted: str
    is_dwell_time_satisfied: bool
    client_otp_verified: bool
    photo_proof_recorded: bool
    message: str


class BreadcrumbPoint(BaseModel):
    timestamp: datetime
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    speed_kmh: Optional[float] = None
    accuracy_meters: Optional[float] = None
    battery_level: Optional[int] = None
    is_mock: bool = False
    activity_type: str = "IN_VEHICLE"  # STATIONARY, IN_VEHICLE, WALKING, ON_BICYCLE


class BreadcrumbsBatchRequest(BaseModel):
    itinerary_id: Optional[uuid.UUID] = None
    points: List[BreadcrumbPoint] = Field(..., min_length=1)
