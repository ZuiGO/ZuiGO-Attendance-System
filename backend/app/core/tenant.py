"""Multi-tenant resolution middleware and context management."""

import re
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.database import current_tenant_id_ctx


def extract_subdomain(host: str) -> Optional[str]:
    """Extracts subdomain from Host header, excluding localhost/IPs."""
    host_without_port = host.split(":")[0]
    # Check if host is an IP or localhost
    if host_without_port in ("localhost", "127.0.0.1", "0.0.0.0") or re.match(r"^\d+\.\d+\.\d+\.\d+$", host_without_port):
        return None

    parts = host_without_port.split(".")
    if len(parts) >= 3:
        # e.g., acme.attendance.zuigo.ai -> acme
        return parts[0]
    return None


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that inspects incoming requests and sets the current tenant context.
    Resolution priority:
      1. X-Tenant-ID HTTP header
      2. Subdomain in Host header
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_id = request.headers.get("X-Tenant-ID")

        if not tenant_id:
            host = request.headers.get("Host", "")
            subdomain = extract_subdomain(host)
            if subdomain:
                tenant_id = subdomain

        # Set tenant in request state and contextvar
        token = current_tenant_id_ctx.set(tenant_id)
        request.state.tenant_id = tenant_id

        try:
            response = await call_next(request)
            if tenant_id:
                response.headers["X-Tenant-ID"] = tenant_id
            return response
        finally:
            current_tenant_id_ctx.reset(token)
