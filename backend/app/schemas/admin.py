"""Pydantic schemas for Employer Admin Dashboard & Analytics."""

from datetime import date, datetime
from typing import Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class LiveEmployeePresence(BaseModel):
    employee_id: str
    employee_name: str
    employee_code: str
    department: str
    office_name: str
    clock_in_time: str
    clock_in_formatted: str
    current_active_task: Optional[str] = None
    active_task_elapsed_seconds: int = 0
    active_task_elapsed_formatted: str = "0m"
    status: str = "WORKING"  # WORKING, IDLE, ON_BREAK, ABSENT
    presence_type: str = "IN_OFFICE"  # IN_OFFICE, ON_FIELD_VISIT, TRAVEL_SHIFT, ABSENT
    network_type: str = "OFFICE_WIFI"  # OFFICE_WIFI, PERSONAL_CELLULAR, OFFLINE
    is_office_wifi: bool = True
    live_location: Optional[str] = None
    last_seen_at: Optional[str] = None


class CreateEmployeeRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: str = Field(..., description="Unique employee login email")
    password: str = Field(..., min_length=6, description="Initial password for login")
    employee_code: str = Field(..., description="Unique employee alphanumeric code e.g. EMP-1005")
    role: str = Field(default="EMPLOYEE", description="ADMIN, MANAGER, or EMPLOYEE")
    department_name: Optional[str] = Field("Field Operations")
    phone: Optional[str] = None
    office_id: Optional[str] = None


class EmployeeItem(BaseModel):
    id: str
    employee_code: str
    full_name: str
    email: str
    role: str
    department: str
    office_name: str
    phone: Optional[str] = None
    is_active: bool
    registered_device_id: Optional[str] = None
    last_seen_at: Optional[str] = None
    current_network_type: Optional[str] = None
    created_at: str


class AssignTaskRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    assigned_to: str = Field(..., description="Employee UUID")
    priority: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, URGENT")
    estimated_hours: Optional[float] = None
    project_id: Optional[str] = None


class AdminTaskItem(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    assigned_to_id: Optional[str] = None
    assigned_to_name: Optional[str] = None
    priority: str
    status: str
    estimated_hours: Optional[float] = None
    project_name: str
    created_at: str
    active_stopwatch_running: bool = False
    active_seconds: int = 0


class UserActivityLogItem(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    employee_code: str
    activity_type: str
    description: str
    network_type: str
    is_office_wifi: bool
    ip_address: Optional[str] = None
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    metadata: Dict = {}
    created_at: str
    created_at_formatted: str


class LivePresenceBoardResponse(BaseModel):
    total_expected: int
    total_present: int
    total_absent: int
    presence_rate_pct: float
    total_active_tasks: int
    employees: List[LiveEmployeePresence]


class FieldStaffRouteStatus(BaseModel):
    employee_id: str
    employee_name: str
    itinerary_id: str
    itinerary_title: str
    total_planned_stops: int
    completed_stops: int
    current_stop_name: Optional[str] = None
    current_stop_dwell_seconds: int = 0
    current_stop_dwell_formatted: str = "0m"
    has_unauthorized_detour: bool = False
    has_drive_by_exception: bool = False


class TravelReimbursementItem(BaseModel):
    travel_log_id: str
    employee_id: str
    employee_name: str
    transport_mode: str
    shift_date: str
    odometer_distance_km: Optional[float] = None
    gps_distance_km: float
    discrepancy_pct: Optional[float] = None
    is_discrepancy_flagged: bool
    reimbursement_rate_per_km: float
    reimbursement_amount: float
    status: str  # PENDING, APPROVED, REJECTED, PAID


class ApproveReimbursementRequest(BaseModel):
    action: str = Field(..., description="APPROVE or REJECT")
    approved_amount: Optional[float] = None
    reviewer_notes: Optional[str] = None


class TenantPolicyUpdate(BaseModel):
    grace_period_minutes: Optional[int] = Field(None, ge=0, le=60)
    field_visit_default_dwell_minutes: Optional[int] = Field(None, ge=5, le=120)
    odometer_discrepancy_threshold_pct: Optional[float] = Field(None, ge=1.0, le=50.0)
    car_reimbursement_rate: Optional[float] = Field(None, ge=0.0)
    bike_reimbursement_rate: Optional[float] = Field(None, ge=0.0)


class OfficeItem(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    allowed_radius_meters: int
    allowed_bssid_list: List[str] = []
    kiosk_api_key: Optional[str] = None
    is_active: bool


class CreateOfficeRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    address: Optional[str] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    allowed_radius_meters: int = Field(default=50, ge=10, le=500)
    allowed_bssid_list: List[str] = []
    kiosk_api_key: Optional[str] = None


class DestinationItem(BaseModel):
    id: str
    name: str
    client_type: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    otp_channel: str = "SMS"
    address: Optional[str] = None
    latitude: float
    longitude: float
    geofence_radius_meters: int = 75
    min_dwell_minutes: int = 30
    is_active: bool


class CreateDestinationRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    client_type: str = Field(default="HOSPITAL")
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    otp_channel: str = Field(default="SMS")
    address: Optional[str] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    geofence_radius_meters: int = Field(default=75, ge=10, le=1000)
    min_dwell_minutes: int = Field(default=30, ge=5, le=180)


class FieldBeatItem(BaseModel):
    id: str
    destination_name: str
    client_type: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    employee_name: str
    geofence_status: str
    dwell_status: str
    otp_status: str
    status: str

