"""Kiosk API endpoints: WebSocket stream and HTTP poll for laptop screen QR display."""

import asyncio
from datetime import datetime, timezone
import json
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis_client
from app.models.tenant import Office, Tenant
from app.schemas.kiosk import DynamicQRPayload, KioskQRStreamMessage
from app.services.qr_service import DynamicQRService

router = APIRouter(prefix="/kiosk", tags=["Office Kiosk Display"])


async def get_qr_service() -> DynamicQRService:
    """Dependency that supplies an initialized DynamicQRService."""
    try:
        redis_client = await get_redis_client()
    except Exception:
        redis_client = None
    return DynamicQRService(redis_client=redis_client)


@router.get("/current-qr", response_model=KioskQRStreamMessage)
async def get_current_kiosk_qr(
    kiosk_key: Annotated[str, Query(description="Secret API key assigned to the office kiosk laptop")],
    db: Annotated[AsyncSession, Depends(get_db)],
    qr_service: Annotated[DynamicQRService, Depends(get_qr_service)],
):
    """
    HTTP endpoint for initial load or polling-based laptop kiosk displays.
    Generates a cryptographically signed dynamic QR token valid for 15 seconds.
    """
    # Look up the office by kiosk_api_key
    stmt = select(Office, Tenant).join(Tenant, Office.tenant_id == Tenant.id).where(Office.kiosk_api_key == kiosk_key, Office.is_active.is_(True))
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or deactivated kiosk API key",
        )
    office, tenant = row

    payload = await qr_service.generate_qr_for_office(
        tenant_id=str(office.tenant_id),
        office_id=str(office.id),
    )

    return KioskQRStreamMessage(
        type="QR_REFRESH",
        office_name=office.name,
        tenant_name=tenant.name,
        data=payload,
        server_time=datetime.now(timezone.utc).isoformat(),
    )


@router.websocket("/qr-stream")
async def kiosk_qr_websocket(
    websocket: WebSocket,
    kiosk_key: str = Query(...),
):
    """
    High-performance WebSocket stream for laptop screen kiosk.
    Pushes a freshly generated signed dynamic QR code every 15 seconds.
    """
    await websocket.accept()

    try:
        qr_service = await get_qr_service()

        while True:
            # Generate new dynamic QR token
            # In a live setup, resolve office_id from kiosk_key
            payload = await qr_service.generate_qr_for_office(
                tenant_id="default-tenant",
                office_id=kiosk_key,
            )

            msg = KioskQRStreamMessage(
                type="QR_REFRESH",
                office_name="Office Main Terminal",
                tenant_name="ZuiGO",
                data=payload,
                server_time=datetime.now(timezone.utc).isoformat(),
            )

            await websocket.send_json(msg.model_dump())
            # Sleep for 15 seconds before rotating to next QR code
            await asyncio.sleep(15)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception:
            pass
