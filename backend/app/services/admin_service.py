"""Employer Admin Dashboard & Analytics Service."""

from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRecord
from app.models.employee import Department, Employee
from app.models.field_visit import FieldItinerary, FieldVisitStop
from app.models.task import Task, TaskTimeEntry
from app.models.tenant import Office, Tenant
from app.models.travel import TravelLog
from app.schemas.admin import (
    ApproveReimbursementRequest,
    FieldStaffRouteStatus,
    LiveEmployeePresence,
    LivePresenceBoardResponse,
    TenantPolicyUpdate,
    TravelReimbursementItem,
)
from app.services.task_service import format_seconds


class AdminDashboardService:
    """Service providing real-time presence boards, field audit, and reimbursement approvals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_live_presence_board(self, tenant_id: uuid.UUID) -> LivePresenceBoardResponse:
        """
        Aggregates real-time presence data:
          - Who is in office right now
          - Arrival timestamps
          - Currently running active task ticker
        """
        today = date.today()
        now = datetime.now(timezone.utc)

        # Total active employees in tenant
        emp_count_stmt = select(func.count(Employee.id)).where(
            Employee.tenant_id == tenant_id,
            Employee.is_active.is_(True),
        )
        total_expected = (await self.db.execute(emp_count_stmt)).scalar() or 0

        # Query present attendance records today (clock_out is None)
        att_stmt = (
            select(AttendanceRecord, Employee, Office, Department)
            .join(Employee, AttendanceRecord.employee_id == Employee.id)
            .join(Office, AttendanceRecord.office_id == Office.id)
            .outerjoin(Department, Employee.department_id == Department.id)
            .where(
                AttendanceRecord.tenant_id == tenant_id,
                AttendanceRecord.date == today,
                AttendanceRecord.clock_out.is_(None),
            )
        )
        att_rows = (await self.db.execute(att_stmt)).all()
        total_present = len(att_rows)
        total_absent = max(0, total_expected - total_present)
        presence_rate = round((total_present / total_expected * 100.0), 1) if total_expected > 0 else 0.0

        # Active tasks
        active_tasks_stmt = (
            select(TaskTimeEntry, Task)
            .join(Task, TaskTimeEntry.task_id == Task.id)
            .where(
                TaskTimeEntry.tenant_id == tenant_id,
                TaskTimeEntry.end_time.is_(None),
            )
        )
        active_task_rows = (await self.db.execute(active_tasks_stmt)).all()
        active_task_map = {}
        for entry, task in active_task_rows:
            elapsed = int((now - entry.start_time).total_seconds())
            active_task_map[entry.employee_id] = (task.title, elapsed)

        employee_items: List[LiveEmployeePresence] = []
        for att, emp, office, dept in att_rows:
            active_task_info = active_task_map.get(emp.id)
            current_task_title = active_task_info[0] if active_task_info else None
            elapsed_sec = active_task_info[1] if active_task_info else 0

            employee_items.append(
                LiveEmployeePresence(
                    employee_id=str(emp.id),
                    employee_name=emp.full_name,
                    employee_code=emp.employee_code,
                    department=dept.name if dept else "General",
                    office_name=office.name,
                    clock_in_time=att.clock_in.isoformat(),
                    clock_in_formatted=att.clock_in.strftime("%I:%M %p"),
                    current_active_task=current_task_title,
                    active_task_elapsed_seconds=elapsed_sec,
                    active_task_elapsed_formatted=format_seconds(elapsed_sec),
                    status="WORKING" if current_task_title else "IDLE",
                )
            )

        return LivePresenceBoardResponse(
            total_expected=total_expected,
            total_present=total_present,
            total_absent=total_absent,
            presence_rate_pct=presence_rate,
            total_active_tasks=len(active_task_rows),
            employees=employee_items,
        )

    async def get_travel_reimbursements(
        self,
        tenant_id: uuid.UUID,
        status_filter: Optional[str] = None,
    ) -> List[TravelReimbursementItem]:
        """Fetches mileage claims with odometer vs GPS discrepancy flags."""
        stmt = (
            select(TravelLog, Employee)
            .join(Employee, TravelLog.employee_id == Employee.id)
            .where(TravelLog.tenant_id == tenant_id)
            .order_by(TravelLog.shift_start_time.desc())
        )
        if status_filter:
            stmt = stmt.where(TravelLog.reimbursement_status == status_filter)

        rows = (await self.db.execute(stmt)).all()
        results: List[TravelReimbursementItem] = []
        for log, emp in rows:
            results.append(
                TravelReimbursementItem(
                    travel_log_id=str(log.id),
                    employee_id=str(emp.id),
                    employee_name=emp.full_name,
                    transport_mode=log.transport_mode,
                    shift_date=log.shift_start_time.strftime("%Y-%m-%d"),
                    odometer_distance_km=float(log.odometer_distance_km) if log.odometer_distance_km else None,
                    gps_distance_km=float(log.gps_total_distance_km or 0.0),
                    discrepancy_pct=float(log.distance_discrepancy_pct) if log.distance_discrepancy_pct else None,
                    is_discrepancy_flagged=log.is_discrepancy_flagged,
                    reimbursement_rate_per_km=float(log.reimbursement_rate_per_km),
                    reimbursement_amount=float(log.reimbursement_amount),
                    status=log.reimbursement_status,
                )
            )
        return results

    async def update_reimbursement_status(
        self,
        tenant_id: uuid.UUID,
        travel_log_id: uuid.UUID,
        data: ApproveReimbursementRequest,
    ) -> Tuple[bool, Optional[str]]:
        """Approves or rejects an employee travel reimbursement."""
        stmt = select(TravelLog).where(TravelLog.id == travel_log_id, TravelLog.tenant_id == tenant_id)
        res = await self.db.execute(stmt)
        log = res.scalar_one_or_none()
        if not log:
            return False, "TRAVEL_LOG_NOT_FOUND"

        if data.action == "APPROVE":
            log.reimbursement_status = "APPROVED"
            if data.approved_amount is not None:
                log.reimbursement_amount = data.approved_amount
        elif data.action == "REJECT":
            log.reimbursement_status = "REJECTED"
        else:
            return False, "INVALID_ACTION (must be APPROVE or REJECT)"

        await self.db.commit()
        return True, None

    async def update_tenant_policy(
        self,
        tenant_id: uuid.UUID,
        data: TenantPolicyUpdate,
    ) -> Tuple[bool, Optional[dict]]:
        """Updates employer-configurable policies (Dwell time, grace period, reimbursement rates)."""
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        res = await self.db.execute(stmt)
        tenant = res.scalar_one_or_none()
        if not tenant:
            return False, None

        cfg = dict(tenant.configuration or {})

        if data.grace_period_minutes is not None:
            cfg["grace_period_minutes"] = data.grace_period_minutes
        if data.field_visit_default_dwell_minutes is not None:
            cfg["field_visit_default_dwell_minutes"] = data.field_visit_default_dwell_minutes
        if data.odometer_discrepancy_threshold_pct is not None:
            cfg["odometer_discrepancy_threshold_pct"] = data.odometer_discrepancy_threshold_pct

        if "travel_reimbursement_rates" not in cfg:
            cfg["travel_reimbursement_rates"] = {}
        if data.car_reimbursement_rate is not None:
            cfg["travel_reimbursement_rates"]["PERSONAL_CAR"] = data.car_reimbursement_rate
        if data.bike_reimbursement_rate is not None:
            cfg["travel_reimbursement_rates"]["TWO_WHEELER"] = data.bike_reimbursement_rate

        tenant.configuration = cfg
        await self.db.commit()
        return True, cfg
