"""Employer Admin Dashboard & Analytics Service."""

from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.attendance import AttendanceRecord
from app.models.employee import Department, Employee
from app.models.field_visit import ClientDestination, FieldItinerary, FieldVisitStop
from app.models.task import Project, Task, TaskTimeEntry
from app.models.tenant import Office, Tenant
from app.models.travel import TravelLog
from app.schemas.admin import (
    AdminTaskItem,
    ApproveReimbursementRequest,
    AssignTaskRequest,
    CreateEmployeeRequest,
    EmployeeItem,
    FieldStaffRouteStatus,
    LiveEmployeePresence,
    LivePresenceBoardResponse,
    TenantPolicyUpdate,
    TravelReimbursementItem,
    UserActivityLogItem,
)
from app.services.activity_service import ActivityService
from app.services.task_service import format_seconds


class AdminDashboardService:
    """Service providing real-time presence boards, employee CRUD, task assignment, field audit, and reimbursement approvals."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.activity_service = ActivityService(db=db)

    async def get_live_presence_board(self, tenant_id: uuid.UUID) -> LivePresenceBoardResponse:
        """
        Aggregates real-time presence data across ALL employees:
          - Office presence (with Office Wi-Fi vs Personal Internet indicator)
          - Field visit active presence & dwell tracking
          - Travel shift transit presence
          - Current active task / what the employee is working with
          - Live location coordinates / office / destination
        """
        today = date.today()
        now = datetime.now(timezone.utc)

        # 1. Fetch all active employees in tenant with their department and office
        emp_stmt = (
            select(Employee, Department, Office)
            .outerjoin(Department, Employee.department_id == Department.id)
            .outerjoin(Office, Employee.office_id == Office.id)
            .where(Employee.tenant_id == tenant_id, Employee.is_active.is_(True))
            .order_by(Employee.full_name.asc())
        )
        emp_rows = (await self.db.execute(emp_stmt)).all()
        total_expected = len(emp_rows)

        # 2. Query present attendance records today (clock_out is None)
        att_stmt = (
            select(AttendanceRecord, Office)
            .join(Office, AttendanceRecord.office_id == Office.id)
            .where(
                AttendanceRecord.tenant_id == tenant_id,
                AttendanceRecord.date == today,
                AttendanceRecord.clock_out.is_(None),
            )
        )
        att_rows = (await self.db.execute(att_stmt)).all()
        att_map = {att.employee_id: (att, office) for att, office in att_rows}

        # 3. Active running tasks
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

        # 4. Active field visits / stops
        field_stmt = (
            select(FieldItinerary, FieldVisitStop, ClientDestination)
            .join(FieldVisitStop, FieldVisitStop.itinerary_id == FieldItinerary.id)
            .join(ClientDestination, FieldVisitStop.destination_id == ClientDestination.id)
            .where(
                FieldItinerary.tenant_id == tenant_id,
                FieldItinerary.date == today,
                FieldVisitStop.status == "ARRIVED",
            )
        )
        field_rows = (await self.db.execute(field_stmt)).all()
        field_map = {}
        for itin, stop, dest in field_rows:
            dwell_sec = int((now - stop.actual_arrival_time).total_seconds()) if stop.actual_arrival_time else 0
            field_map[itin.employee_id] = (dest.name, dest.client_type, dwell_sec, stop.is_geofence_verified)

        # 5. Active travel logs
        travel_stmt = (
            select(TravelLog)
            .where(
                TravelLog.tenant_id == tenant_id,
                TravelLog.status == "ACTIVE",
            )
        )
        travel_rows = (await self.db.execute(travel_stmt)).scalars().all()
        travel_map = {log.employee_id: log for log in travel_rows}

        employee_items: List[LiveEmployeePresence] = []
        total_present = 0

        for emp, dept, emp_office in emp_rows:
            dept_name = dept.name if dept else "General"
            office_name = emp_office.name if emp_office else "Cyber City HQ"

            if emp.id in att_map:
                att, office = att_map[emp.id]
                total_present += 1
                task_info = active_task_map.get(emp.id)
                task_title = task_info[0] if task_info else None
                task_elapsed = task_info[1] if task_info else 0

                is_wifi = getattr(att, "clock_in_is_office_wifi", True)
                if is_wifi is None:
                    is_wifi = True
                net_type = getattr(att, "clock_in_network_type", "OFFICE_WIFI") or "OFFICE_WIFI"

                employee_items.append(
                    LiveEmployeePresence(
                        employee_id=str(emp.id),
                        employee_name=emp.full_name,
                        employee_code=emp.employee_code,
                        department=dept_name,
                        office_name=office.name,
                        clock_in_time=att.clock_in.isoformat(),
                        clock_in_formatted=att.clock_in.strftime("%I:%M %p"),
                        current_active_task=task_title or "Present in Office (Standby)",
                        active_task_elapsed_seconds=task_elapsed,
                        active_task_elapsed_formatted=format_seconds(task_elapsed) if task_title else "0m",
                        status="WORKING" if task_title else "IDLE",
                        presence_type="IN_OFFICE",
                        network_type=net_type,
                        is_office_wifi=is_wifi,
                        live_location=f"In Office: {office.name}",
                        last_seen_at=emp.last_seen_at.isoformat() if emp.last_seen_at else att.clock_in.isoformat(),
                    )
                )
            elif emp.id in field_map:
                total_present += 1
                dest_name, client_type, dwell_sec, otp_verified = field_map[emp.id]
                status_desc = f"Visiting {dest_name} ({client_type})"
                employee_items.append(
                    LiveEmployeePresence(
                        employee_id=str(emp.id),
                        employee_name=emp.full_name,
                        employee_code=emp.employee_code,
                        department=dept_name,
                        office_name=office_name,
                        clock_in_time=now.isoformat(),
                        clock_in_formatted="On Field",
                        current_active_task=status_desc,
                        active_task_elapsed_seconds=dwell_sec,
                        active_task_elapsed_formatted=format_seconds(dwell_sec),
                        status="WORKING",
                        presence_type="ON_FIELD_VISIT",
                        network_type=emp.current_network_type or "PERSONAL_CELLULAR",
                        is_office_wifi=False,
                        live_location=f"Field Client: {dest_name}",
                        last_seen_at=emp.last_seen_at.isoformat() if emp.last_seen_at else now.isoformat(),
                    )
                )
            elif emp.id in travel_map:
                total_present += 1
                t_log = travel_map[emp.id]
                status_desc = f"In Transit ({t_log.transport_mode})"
                elapsed_sec = int((now - t_log.shift_start_time).total_seconds())
                employee_items.append(
                    LiveEmployeePresence(
                        employee_id=str(emp.id),
                        employee_name=emp.full_name,
                        employee_code=emp.employee_code,
                        department=dept_name,
                        office_name=office_name,
                        clock_in_time=t_log.shift_start_time.isoformat(),
                        clock_in_formatted=t_log.shift_start_time.strftime("%I:%M %p"),
                        current_active_task=status_desc,
                        active_task_elapsed_seconds=elapsed_sec,
                        active_task_elapsed_formatted=format_seconds(elapsed_sec),
                        status="WORKING",
                        presence_type="TRAVEL_SHIFT",
                        network_type=emp.current_network_type or "PERSONAL_CELLULAR",
                        is_office_wifi=False,
                        live_location="Transit Route (GPS)",
                        last_seen_at=emp.last_seen_at.isoformat() if emp.last_seen_at else now.isoformat(),
                    )
                )
            else:
                employee_items.append(
                    LiveEmployeePresence(
                        employee_id=str(emp.id),
                        employee_name=emp.full_name,
                        employee_code=emp.employee_code,
                        department=dept_name,
                        office_name=office_name,
                        clock_in_time="",
                        clock_in_formatted="--",
                        current_active_task=None,
                        active_task_elapsed_seconds=0,
                        active_task_elapsed_formatted="--",
                        status="ABSENT",
                        presence_type="ABSENT",
                        network_type="OFFLINE",
                        is_office_wifi=False,
                        live_location="Off-Duty / Absent",
                        last_seen_at=emp.last_seen_at.isoformat() if emp.last_seen_at else None,
                    )
                )

        total_absent = max(0, total_expected - total_present)
        presence_rate = round((total_present / total_expected * 100.0), 1) if total_expected > 0 else 0.0

        return LivePresenceBoardResponse(
            total_expected=total_expected,
            total_present=total_present,
            total_absent=total_absent,
            presence_rate_pct=presence_rate,
            total_active_tasks=len(active_task_rows),
            employees=employee_items,
        )

    async def get_employees(self, tenant_id: uuid.UUID) -> List[EmployeeItem]:
        """Lists all employees in tenant for management."""
        stmt = (
            select(Employee, Department, Office)
            .outerjoin(Department, Employee.department_id == Department.id)
            .outerjoin(Office, Employee.office_id == Office.id)
            .where(Employee.tenant_id == tenant_id)
            .order_by(Employee.created_at.desc())
        )
        rows = (await self.db.execute(stmt)).all()
        results = []
        for emp, dept, off in rows:
            results.append(
                EmployeeItem(
                    id=str(emp.id),
                    employee_code=emp.employee_code,
                    full_name=emp.full_name,
                    email=emp.email,
                    role=emp.role,
                    department=dept.name if dept else "General",
                    office_name=off.name if off else "Cyber City HQ",
                    phone=emp.phone,
                    is_active=emp.is_active,
                    registered_device_id=emp.registered_device_id,
                    last_seen_at=emp.last_seen_at.isoformat() if emp.last_seen_at else None,
                    current_network_type=emp.current_network_type,
                    created_at=emp.created_at.isoformat(),
                )
            )
        return results

    async def create_employee(
        self,
        tenant_id: uuid.UUID,
        data: CreateEmployeeRequest,
    ) -> Tuple[bool, Optional[str], Optional[EmployeeItem]]:
        """Creates a new employee profile with credentials and department linkage."""
        email_clean = data.email.lower().strip()
        code_clean = data.employee_code.upper().strip()

        # Check email uniqueness
        email_check = select(Employee).where(Employee.tenant_id == tenant_id, Employee.email == email_clean)
        if (await self.db.execute(email_check)).scalar_one_or_none():
            return False, f"Employee with email '{email_clean}' already exists", None

        # Check code uniqueness
        code_check = select(Employee).where(Employee.tenant_id == tenant_id, Employee.employee_code == code_clean)
        if (await self.db.execute(code_check)).scalar_one_or_none():
            return False, f"Employee code '{code_clean}' already exists", None

        # Department resolution
        dept_name = data.department_name or "Field Operations"
        dept_stmt = select(Department).where(Department.tenant_id == tenant_id, Department.name == dept_name)
        dept = (await self.db.execute(dept_stmt)).scalar_one_or_none()
        if not dept:
            dept = Department(id=uuid.uuid4(), tenant_id=tenant_id, name=dept_name)
            self.db.add(dept)
            await self.db.flush()

        # Office resolution
        office_id = None
        if data.office_id:
            try:
                office_id = uuid.UUID(data.office_id)
            except ValueError:
                pass
        if not office_id:
            off_stmt = select(Office).where(Office.tenant_id == tenant_id).limit(1)
            first_off = (await self.db.execute(off_stmt)).scalar_one_or_none()
            if first_off:
                office_id = first_off.id

        hashed_pw = get_password_hash(data.password)
        now_utc = datetime.now(timezone.utc)
        new_emp = Employee(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            office_id=office_id,
            department_id=dept.id,
            employee_code=code_clean,
            full_name=data.full_name.strip(),
            email=email_clean,
            hashed_password=hashed_pw,
            phone=data.phone,
            role=data.role.upper().strip(),
            is_active=True,
            created_at=now_utc,
        )
        self.db.add(new_emp)
        await self.db.commit()
        await self.db.refresh(new_emp)

        # Log Activity
        await self.activity_service.log_activity(
            tenant_id=tenant_id,
            employee_id=new_emp.id,
            activity_type="EMPLOYEE_CREATED",
            description=f"Created employee {new_emp.full_name} ({new_emp.employee_code}) with role {new_emp.role}",
            network_type="ADMIN_PORTAL",
            is_office_wifi=True,
            metadata_json={"email": new_emp.email, "role": new_emp.role, "code": new_emp.employee_code},
        )

        office_name = "Cyber City HQ"
        if office_id:
            off = await self.db.get(Office, office_id)
            if off:
                office_name = off.name

        item = EmployeeItem(
            id=str(new_emp.id),
            employee_code=new_emp.employee_code,
            full_name=new_emp.full_name,
            email=new_emp.email,
            role=new_emp.role,
            department=dept.name,
            office_name=office_name,
            phone=new_emp.phone,
            is_active=new_emp.is_active,
            registered_device_id=new_emp.registered_device_id,
            last_seen_at=None,
            current_network_type=None,
            created_at=(new_emp.created_at or now_utc).isoformat(),
        )
        return True, None, item

    async def delete_employee(
        self,
        tenant_id: uuid.UUID,
        employee_id: uuid.UUID,
    ) -> Tuple[bool, Optional[str]]:
        """Deactivates an employee account and halts running timers."""
        emp = await self.db.get(Employee, employee_id)
        if not emp or emp.tenant_id != tenant_id:
            return False, "EMPLOYEE_NOT_FOUND"

        emp.is_active = False

        # Close any running task time entries
        now = datetime.now(timezone.utc)
        active_entries = (await self.db.execute(
            select(TaskTimeEntry).where(TaskTimeEntry.employee_id == employee_id, TaskTimeEntry.end_time.is_(None))
        )).scalars().all()
        for entry in active_entries:
            entry.end_time = now

        # Log Activity
        await self.activity_service.log_activity(
            tenant_id=tenant_id,
            employee_id=employee_id,
            activity_type="EMPLOYEE_DEACTIVATED",
            description=f"Admin deactivated employee profile {emp.full_name} ({emp.employee_code})",
            network_type="ADMIN_PORTAL",
            is_office_wifi=True,
            metadata_json={"employee_name": emp.full_name, "code": emp.employee_code},
        )

        await self.db.commit()
        return True, None

    async def assign_task(
        self,
        tenant_id: uuid.UUID,
        data: AssignTaskRequest,
    ) -> Tuple[bool, Optional[str], Optional[AdminTaskItem]]:
        """Creates and assigns a task to an employee."""
        emp_uuid = uuid.UUID(data.assigned_to)
        emp = await self.db.get(Employee, emp_uuid)
        if not emp or emp.tenant_id != tenant_id:
            return False, "ASSIGNEE_NOT_FOUND", None

        # Resolve project
        proj_id = None
        if data.project_id:
            try:
                proj_id = uuid.UUID(data.project_id)
            except ValueError:
                pass
        if not proj_id:
            proj_stmt = select(Project).where(Project.tenant_id == tenant_id).limit(1)
            proj = (await self.db.execute(proj_stmt)).scalar_one_or_none()
            if not proj:
                proj = Project(id=uuid.uuid4(), tenant_id=tenant_id, name="Field Operations & Client Care", is_active=True)
                self.db.add(proj)
                await self.db.flush()
            proj_id = proj.id

        now_utc = datetime.now(timezone.utc)
        new_task = Task(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            project_id=proj_id,
            title=data.title.strip(),
            description=data.description,
            assigned_to=emp_uuid,
            priority=data.priority.upper().strip(),
            status="TODO",
            estimated_hours=data.estimated_hours,
            created_at=now_utc,
        )
        self.db.add(new_task)
        await self.db.commit()
        await self.db.refresh(new_task)

        proj = await self.db.get(Project, proj_id)

        # Log Activity
        await self.activity_service.log_activity(
            tenant_id=tenant_id,
            employee_id=emp_uuid,
            activity_type="TASK_ASSIGNED",
            description=f"Admin assigned new task '{new_task.title}' to {emp.full_name} (Priority: {new_task.priority})",
            network_type="ADMIN_PORTAL",
            is_office_wifi=True,
            metadata_json={"task_title": new_task.title, "priority": new_task.priority},
        )

        item = AdminTaskItem(
            id=str(new_task.id),
            title=new_task.title,
            description=new_task.description,
            assigned_to_id=str(emp.id),
            assigned_to_name=emp.full_name,
            priority=new_task.priority,
            status=new_task.status,
            estimated_hours=float(new_task.estimated_hours) if new_task.estimated_hours else None,
            project_name=proj.name if proj else "Operations",
            created_at=(new_task.created_at or now_utc).isoformat(),
            active_stopwatch_running=False,
            active_seconds=0,
        )
        return True, None, item

    async def get_admin_tasks(self, tenant_id: uuid.UUID) -> List[AdminTaskItem]:
        """Lists all tasks with assigned employee name and stopwatch status."""
        stmt = (
            select(Task, Employee, Project)
            .outerjoin(Employee, Task.assigned_to == Employee.id)
            .join(Project, Task.project_id == Project.id)
            .where(Task.tenant_id == tenant_id)
            .order_by(Task.created_at.desc())
        )
        rows = (await self.db.execute(stmt)).all()

        now = datetime.now(timezone.utc)
        active_stmt = select(TaskTimeEntry).where(TaskTimeEntry.tenant_id == tenant_id, TaskTimeEntry.end_time.is_(None))
        active_entries = (await self.db.execute(active_stmt)).scalars().all()
        active_map = {entry.task_id: int((now - entry.start_time).total_seconds()) for entry in active_entries}

        results = []
        for task, emp, proj in rows:
            is_running = task.id in active_map
            active_sec = active_map.get(task.id, 0)
            results.append(
                AdminTaskItem(
                    id=str(task.id),
                    title=task.title,
                    description=task.description,
                    assigned_to_id=str(emp.id) if emp else None,
                    assigned_to_name=emp.full_name if emp else "Unassigned",
                    priority=task.priority,
                    status="IN_PROGRESS" if is_running else task.status,
                    estimated_hours=float(task.estimated_hours) if task.estimated_hours else None,
                    project_name=proj.name,
                    created_at=task.created_at.isoformat(),
                    active_stopwatch_running=is_running,
                    active_seconds=active_sec,
                )
            )
        return results

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
