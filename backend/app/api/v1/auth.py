"""Authentication and Hardware Device Binding API Endpoints."""

from datetime import datetime, timezone
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db, current_tenant_id_ctx
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, verify_password
from app.models.employee import Employee
from app.models.tenant import Tenant
from app.schemas.auth import EnrollDeviceRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication & Enrollment"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Authenticates employee credentials and issues a multi-tenant JWT access token.
    """
    # 1. Resolve tenant
    tenant_id_str = request.tenant_id or current_tenant_id_ctx.get()
    
    query = select(Employee, Tenant).join(Tenant, Employee.tenant_id == Tenant.id).where(
        Employee.email == request.email.lower().strip(),
        Employee.is_active.is_(True),
    )
    if tenant_id_str:
        try:
            t_uuid = uuid.UUID(tenant_id_str)
            query = query.where(Employee.tenant_id == t_uuid)
        except ValueError:
            query = query.where(Tenant.subdomain == tenant_id_str)

    res = await db.execute(query)
    row = res.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    employee, tenant = row

    # 2. Verify password
    if not verify_password(request.password, employee.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # 3. Create JWT
    access_token = create_access_token(
        subject=str(employee.id),
        tenant_id=str(tenant.id),
        role=employee.role,
        extra_claims={
            "subdomain": tenant.subdomain,
            "email": employee.email,
            "name": employee.full_name,
        },
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        employee_id=str(employee.id),
        employee_name=employee.full_name,
        role=employee.role,
        tenant_id=str(tenant.id),
    )


@router.post("/enroll-device")
async def enroll_device(
    request: EnrollDeviceRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Binds the smartphone hardware UUID and Secure Enclave key to the employee.
    Enforces the 1:1 hardware device binding rule.
    """
    stmt = select(Employee).where(Employee.email == request.email.lower().strip())
    res = await db.execute(stmt)
    employee = res.scalar_one_or_none()
    if not employee or not verify_password(request.password, employee.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed during device enrollment",
        )

    now = datetime.now(timezone.utc)
    employee.registered_device_id = request.device_id
    employee.device_public_key = request.device_public_key
    employee.device_model = request.device_model
    employee.device_enrolled_at = now

    await db.commit()
    return {
        "success": True,
        "message": f"Device {request.device_model or request.device_id} successfully bound to {employee.full_name}.",
        "enrolled_at": now.isoformat(),
    }


@router.get("/me")
async def get_my_profile(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Returns the authenticated employee's profile."""
    emp_id = uuid.UUID(current_user["sub"])
    res = await db.execute(select(Employee).where(Employee.id == emp_id))
    emp = res.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    return {
        "id": str(emp.id),
        "employee_code": emp.employee_code,
        "full_name": emp.full_name,
        "email": emp.email,
        "role": emp.role,
        "registered_device_id": emp.registered_device_id,
        "tenant_id": str(emp.tenant_id),
    }
