"""Employer Admin API endpoints for Live Presence, Reimbursements, and Policy Configuration."""

from typing import Annotated, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.schemas.admin import (
    ApproveReimbursementRequest,
    LivePresenceBoardResponse,
    TenantPolicyUpdate,
    TravelReimbursementItem,
)
from app.services.admin_service import AdminDashboardService

router = APIRouter(prefix="/admin", tags=["Employer Admin Dashboard & Approvals"])


def get_admin_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AdminDashboardService:
    return AdminDashboardService(db=db)


@router.get("/presence/live", response_model=LivePresenceBoardResponse)
async def get_live_presence_board(
    current_user: Annotated[dict, Depends(require_role(["ADMIN", "MANAGER"]))],
    admin_service: Annotated[AdminDashboardService, Depends(get_admin_service)],
):
    """
    Live Office Presence Board:
      - Who is in office right now
      - Arrival timestamps
      - Current active task & elapsed stopwatch ticker
    """
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await admin_service.get_live_presence_board(tenant_id=tenant_id)


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
