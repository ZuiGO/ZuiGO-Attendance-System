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
    status: str = "WORKING"  # WORKING, IDLE, ON_BREAK


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
