"""FastAPI dependencies for authentication, tenant context, and authorization."""

from typing import Annotated, List, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.core.config import settings
from app.core.database import current_tenant_id_ctx, get_db
from app.core.redis import get_redis_client
from app.core.security import decode_token

security_bearer = HTTPBearer(auto_error=False)


async def get_tenant_id() -> str:
    """Returns the current tenant ID or raises 400 Bad Request if missing."""
    tenant_id = current_tenant_id_ctx.get()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing tenant context. Provide 'X-Tenant-ID' header or access via tenant subdomain.",
        )
    return tenant_id


async def get_current_user(
    auth: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security_bearer)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
) -> dict:
    """Validates the JWT token and ensures the user belongs to the current tenant."""
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(auth.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ensure token tenant matches the current request tenant
    token_tenant_id = payload.get("tenant_id")
    if token_tenant_id and str(token_tenant_id) != str(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token tenant does not match request tenant boundary",
        )

    return payload


def require_role(allowed_roles: List[str]):
    """Returns a dependency that checks if the authenticated user has an allowed role."""
    async def role_checker(
        current_user: Annotated[dict, Depends(get_current_user)]
    ) -> dict:
        user_role = current_user.get("role", "EMPLOYEE")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {allowed_roles}",
            )
        return current_user
    return role_checker
