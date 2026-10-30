"""Task and Timesheet management API endpoints."""

from typing import Annotated, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.task import Task
from app.schemas.task import (
    ProjectCreate,
    ProjectResponse,
    StartTimerRequest,
    StopTimerRequest,
    TaskCreate,
    TaskResponse,
    TimeEntryResponse,
)
from app.services.task_service import TaskTrackingService

router = APIRouter(prefix="/tasks", tags=["Task & Time Tracking"])


def get_task_service(db: Annotated[AsyncSession, Depends(get_db)]) -> TaskTrackingService:
    return TaskTrackingService(db=db)


@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    task_service: Annotated[TaskTrackingService, Depends(get_task_service)],
):
    """Creates a new project for the organization."""
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await task_service.create_project(tenant_id=tenant_id, data=data)


@router.post("", response_model=TaskResponse)
async def create_task(
    data: TaskCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    task_service: Annotated[TaskTrackingService, Depends(get_task_service)],
):
    """Creates a new task in a project."""
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await task_service.create_task(tenant_id=tenant_id, data=data)


@router.post("/timer/start", response_model=TimeEntryResponse)
async def start_task_timer(
    data: StartTimerRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    task_service: Annotated[TaskTrackingService, Depends(get_task_service)],
):
    """
    Starts a live task timer.
    GATED: Employee must have marked physical attendance today.
    """
    tenant_id = uuid.UUID(current_user["tenant_id"])
    employee_id = uuid.UUID(current_user["sub"])

    success, error_msg, response = await task_service.start_task_timer(
        tenant_id=tenant_id,
        employee_id=employee_id,
        data=data,
    )
    if not success:
        if "ATTENDANCE_REQUIRED" in str(error_msg):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    return response


@router.post("/timer/stop", response_model=TimeEntryResponse)
async def stop_task_timer(
    data: StopTimerRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    task_service: Annotated[TaskTrackingService, Depends(get_task_service)],
):
    """Stops an active task timer and finalizes duration."""
    tenant_id = uuid.UUID(current_user["tenant_id"])
    employee_id = uuid.UUID(current_user["sub"])

    success, error_msg, response = await task_service.stop_task_timer(
        tenant_id=tenant_id,
        employee_id=employee_id,
        data=data,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    return response
