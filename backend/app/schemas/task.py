"""Pydantic schemas for Projects, Tasks, and Attendance-Gated Task Timers."""

from datetime import date, datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    code: Optional[str] = Field(None, max_length=50)


class ProjectResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    code: Optional[str] = None
    is_active: bool
    created_at: str


class TaskCreate(BaseModel):
    project_id: uuid.UUID
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    priority: str = Field(default="MEDIUM")  # LOW, MEDIUM, HIGH, URGENT
    estimated_hours: Optional[float] = None
    due_date: Optional[date] = None


class TaskResponse(BaseModel):
    id: str
    project_id: str
    project_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    status: str  # TODO, IN_PROGRESS, BLOCKED, DONE
    priority: str
    estimated_hours: Optional[float] = None
    total_seconds_tracked: int = 0
    is_timer_running: bool = False


class StartTimerRequest(BaseModel):
    task_id: uuid.UUID
    notes: Optional[str] = None


class StopTimerRequest(BaseModel):
    time_entry_id: uuid.UUID
    notes: Optional[str] = None


class TimeEntryResponse(BaseModel):
    id: str
    task_id: str
    employee_id: str
    attendance_id: Optional[str] = None
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: Optional[int] = None
    duration_formatted: Optional[str] = None
    is_running: bool
    notes: Optional[str] = None
