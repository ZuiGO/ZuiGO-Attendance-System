"""Task and Work Time Tracking Service with Attendance Gating."""

from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRecord
from app.models.task import Project, Task, TaskTimeEntry
from app.schemas.task import (
    ProjectCreate,
    ProjectResponse,
    StartTimerRequest,
    StopTimerRequest,
    TaskCreate,
    TaskResponse,
    TimeEntryResponse,
)


def format_seconds(seconds: int) -> str:
    """Formats seconds into human-readable e.g. '2h 15m' or '45m'."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


class TaskTrackingService:
    """Service managing project tasks and attendance-gated live task timers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(self, tenant_id: uuid.UUID, data: ProjectCreate) -> ProjectResponse:
        """Creates a new project for the tenant."""
        project = Project(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            code=data.code,
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return ProjectResponse(
            id=str(project.id),
            tenant_id=str(project.tenant_id),
            name=project.name,
            description=project.description,
            code=project.code,
            is_active=project.is_active,
            created_at=project.created_at.isoformat(),
        )

    async def create_task(self, tenant_id: uuid.UUID, data: TaskCreate) -> TaskResponse:
        """Creates a new task assigned to an employee or project backlog."""
        task = Task(
            tenant_id=tenant_id,
            project_id=data.project_id,
            title=data.title,
            description=data.description,
            assigned_to=data.assigned_to,
            priority=data.priority,
            estimated_hours=data.estimated_hours,
            due_date=data.due_date,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return TaskResponse(
            id=str(task.id),
            project_id=str(task.project_id),
            title=task.title,
            description=task.description,
            assigned_to=str(task.assigned_to) if task.assigned_to else None,
            status=task.status,
            priority=task.priority,
            estimated_hours=float(task.estimated_hours) if task.estimated_hours else None,
            total_seconds_tracked=0,
            is_timer_running=False,
        )

    async def start_task_timer(
        self,
        tenant_id: uuid.UUID,
        employee_id: uuid.UUID,
        data: StartTimerRequest,
    ) -> Tuple[bool, Optional[str], Optional[TimeEntryResponse]]:
        """
        Starts a task stopwatch timer.
        CRITICAL BUSINESS RULE:
          Must have an active attendance record for today (clocked in, not clocked out).
        """
        # Step 1: Verify Active Daily Attendance
        today = date.today()
        att_stmt = select(AttendanceRecord).where(
            AttendanceRecord.tenant_id == tenant_id,
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.date == today,
            AttendanceRecord.clock_out.is_(None),
        )
        att_res = await self.db.execute(att_stmt)
        active_attendance = att_res.scalar_one_or_none()
        if not active_attendance:
            return False, "ATTENDANCE_REQUIRED: You must be physically clocked in to start a task timer.", None

        # Step 2: Auto-stop any existing running timer for this employee
        now = datetime.now(timezone.utc)
        running_stmt = select(TaskTimeEntry).where(
            TaskTimeEntry.tenant_id == tenant_id,
            TaskTimeEntry.employee_id == employee_id,
            TaskTimeEntry.end_time.is_(None),
        )
        running_res = await self.db.execute(running_stmt)
        existing_running = running_res.scalars().all()
        for active in existing_running:
            active.end_time = now

        # Step 3: Create new task time entry
        new_entry = TaskTimeEntry(
            tenant_id=tenant_id,
            task_id=data.task_id,
            employee_id=employee_id,
            attendance_id=active_attendance.id,
            start_time=now,
            notes=data.notes,
            source="MOBILE_STOPWATCH",
        )
        self.db.add(new_entry)

        # Update task status to IN_PROGRESS
        task_stmt = select(Task).where(Task.id == data.task_id, Task.tenant_id == tenant_id)
        task_res = await self.db.execute(task_stmt)
        task = task_res.scalar_one_or_none()
        if task and task.status == "TODO":
            task.status = "IN_PROGRESS"

        await self.db.commit()
        await self.db.refresh(new_entry)

        response = TimeEntryResponse(
            id=str(new_entry.id),
            task_id=str(new_entry.task_id),
            employee_id=str(new_entry.employee_id),
            attendance_id=str(new_entry.attendance_id) if new_entry.attendance_id else None,
            start_time=new_entry.start_time.isoformat(),
            end_time=None,
            duration_seconds=0,
            duration_formatted="0m",
            is_running=True,
            notes=new_entry.notes,
        )
        return True, None, response

    async def stop_task_timer(
        self,
        tenant_id: uuid.UUID,
        employee_id: uuid.UUID,
        data: StopTimerRequest,
    ) -> Tuple[bool, Optional[str], Optional[TimeEntryResponse]]:
        """Stops an active task timer and finalizes duration."""
        stmt = select(TaskTimeEntry).where(
            TaskTimeEntry.id == data.time_entry_id,
            TaskTimeEntry.tenant_id == tenant_id,
            TaskTimeEntry.employee_id == employee_id,
        )
        res = await self.db.execute(stmt)
        entry = res.scalar_one_or_none()
        if not entry:
            return False, "TIME_ENTRY_NOT_FOUND", None

        if entry.end_time is not None:
            return False, "TIMER_ALREADY_STOPPED", None

        now = datetime.now(timezone.utc)
        entry.end_time = now
        if data.notes:
            entry.notes = f"{entry.notes or ''} | {data.notes}".strip(" |")

        duration_sec = int((now - entry.start_time).total_seconds())

        await self.db.commit()

        response = TimeEntryResponse(
            id=str(entry.id),
            task_id=str(entry.task_id),
            employee_id=str(entry.employee_id),
            attendance_id=str(entry.attendance_id) if entry.attendance_id else None,
            start_time=entry.start_time.isoformat(),
            end_time=now.isoformat(),
            duration_seconds=duration_sec,
            duration_formatted=format_seconds(duration_sec),
            is_running=False,
            notes=entry.notes,
        )
        return True, None, response
