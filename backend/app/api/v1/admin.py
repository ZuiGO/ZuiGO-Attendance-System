"""Employer Admin API endpoints for Live Presence, Employee Management, Task Assignment, Reimbursements, and Audit Logs."""

from typing import Annotated, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.schemas.admin import (
    AdminTaskItem,
    ApproveReimbursementRequest,
    AssignTaskRequest,
    CreateEmployeeRequest,
    EmployeeItem,
    LivePresenceBoardResponse,
    TenantPolicyUpdate,
    TravelReimbursementItem,
    UserActivityLogItem,
)
from app.services.activity_service import ActivityService
from app.services.admin_service import AdminDashboardService

router = APIRouter(prefix="/admin", tags=["Employer Admin Dashboard & Approvals"])


def get_admin_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AdminDashboardService:
    return AdminDashboardService(db=db)


def get_activity_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ActivityService:
    return ActivityService(db=db)


# ==============================================================================
# 1. LIVE PRESENCE & COMMAND CENTER
# ==============================================================================

@router.get("/presence/live", response_model=LivePresenceBoardResponse)
async def get_live_presence_board(
    current_user: Annotated[dict, Depends(require_role(["ADMIN", "MANAGER"]))],
    admin_service: Annotated[AdminDashboardService, Depends(get_admin_service)],
):
    """
    Live Presence Command Center:
      - Live presence state: IN_OFFICE, ON_FIELD_VISIT, TRAVEL_SHIFT, or ABSENT
      - Wi-Fi vs Personal Internet network indicators
      - Current active task / client visit ticker
      - Real-time location coordinates
    """
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await admin_service.get_live_presence_board(tenant_id=tenant_id)


# ==============================================================================
# 2. EMPLOYEE MANAGEMENT (ADD / DELETE)
# ==============================================================================

@router.get("/employees", response_model=List[EmployeeItem])
async def list_employees(
    current_user: Annotated[dict, Depends(require_role(["ADMIN", "MANAGER"]))],
    admin_service: Annotated[AdminDashboardService, Depends(get_admin_service)],
):
    """Lists all registered employees in the organization."""
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await admin_service.get_employees(tenant_id=tenant_id)


@router.post("/employees", response_model=EmployeeItem, status_code=status.HTTP_201_CREATED)
async def create_employee(
    data: CreateEmployeeRequest,
    current_user: Annotated[dict, Depends(require_role(["ADMIN"]))],
    admin_service: Annotated[AdminDashboardService, Depends(get_admin_service)],
):
    """Enrolls a new employee with login credentials, department, and initial role."""
    tenant_id = uuid.UUID(current_user["tenant_id"])
    success, error_msg, item = await admin_service.create_employee(
        tenant_id=tenant_id,
        data=data,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    return item


@router.delete("/employees/{employee_id}")
async def delete_employee(
    employee_id: uuid.UUID,
    current_user: Annotated[dict, Depends(require_role(["ADMIN"]))],
    admin_service: Annotated[AdminDashboardService, Depends(get_admin_service)],
):
    """Deactivates and removes an employee account from active operations."""
    tenant_id = uuid.UUID(current_user["tenant_id"])
    success, error_msg = await admin_service.delete_employee(
        tenant_id=tenant_id,
        employee_id=employee_id,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
    return {"status": "SUCCESS", "message": "Employee deactivated successfully", "employee_id": str(employee_id)}


# ==============================================================================
# 3. TASK ASSIGNMENT & STOPWATCH MONITOR
# ==============================================================================

@router.get("/tasks", response_model=List[AdminTaskItem])
async def list_tasks(
    current_user: Annotated[dict, Depends(require_role(["ADMIN", "MANAGER"]))],
    admin_service: Annotated[AdminDashboardService, Depends(get_admin_service)],
):
    """Lists all operational tasks with assigned employee and live stopwatch status."""
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await admin_service.get_admin_tasks(tenant_id=tenant_id)


@router.post("/tasks", response_model=AdminTaskItem, status_code=status.HTTP_201_CREATED)
async def assign_task(
    data: AssignTaskRequest,
    current_user: Annotated[dict, Depends(require_role(["ADMIN", "MANAGER"]))],
    admin_service: Annotated[AdminDashboardService, Depends(get_admin_service)],
):
    """Creates a new task and assigns it to a specific employee."""
    tenant_id = uuid.UUID(current_user["tenant_id"])
    success, error_msg, task_item = await admin_service.assign_task(
        tenant_id=tenant_id,
        data=data,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    return task_item


# ==============================================================================
# 4. USER ACTIVITY AUDIT TRAIL
# ==============================================================================

@router.get("/activity-logs")
async def get_activity_logs(
    current_user: Annotated[dict, Depends(require_role(["ADMIN", "MANAGER"]))],
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
    employee_id: Annotated[Optional[uuid.UUID], Query()] = None,
    activity_type: Annotated[Optional[str], Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Fetches historical employee activity logs (Clock-ins, Tasks, OTPs, Travel, Network usage)."""
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await activity_service.get_activity_logs(
        tenant_id=tenant_id,
        employee_id=employee_id,
        activity_type=activity_type,
        limit=limit,
        offset=offset,
    )


# ==============================================================================
# 5. TRAVEL REIMBURSEMENTS & POLICY
# ==============================================================================

@router.get("/travel-reimbursements", response_model=List[TravelReimbursementItem])
async def get_travel_reimbursements(
    current_user: Annotated[dict, Depends(require_role(["ADMIN", "MANAGER"]))],
    admin_service: Annotated[AdminDashboardService, Depends(get_admin_service)],
    status_filter: Annotated[Optional[str], Query(description="Filter by PENDING, APPROVED, REJECTED")] = None,
):
    """Fetches employee vehicle travel mileage claims with fraud discrepancy alerts."""
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await admin_service.get_travel_reimbursements(tenant_id=tenant_id, status_filter=status_filter)


@router.post("/travel-reimbursements/{travel_log_id}/action")
async def update_reimbursement_status(
    travel_log_id: uuid.UUID,
    data: ApproveReimbursementRequest,
    current_user: Annotated[dict, Depends(require_role(["ADMIN", "MANAGER"]))],
    admin_service: Annotated[AdminDashboardService, Depends(get_admin_service)],
):
    """Approves or rejects a travel mileage reimbursement claim."""
    tenant_id = uuid.UUID(current_user["tenant_id"])
    success, error_msg = await admin_service.update_reimbursement_status(
        tenant_id=tenant_id,
        travel_log_id=travel_log_id,
        data=data,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    return {"status": "SUCCESS", "action": data.action, "travel_log_id": str(travel_log_id)}


@router.put("/policy")
async def update_tenant_policy(
    data: TenantPolicyUpdate,
    current_user: Annotated[dict, Depends(require_role(["ADMIN"]))],
    admin_service: Annotated[AdminDashboardService, Depends(get_admin_service)],
):
    """Updates employer-configurable policies (Dwell time, grace periods, reimbursement rates)."""
    tenant_id = uuid.UUID(current_user["tenant_id"])
    success, updated_config = await admin_service.update_tenant_policy(
        tenant_id=tenant_id,
        data=data,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    return {"status": "UPDATED", "configuration": updated_config}
