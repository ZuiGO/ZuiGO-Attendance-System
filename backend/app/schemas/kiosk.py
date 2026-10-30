"""Pydantic schemas for the Laptop Screen Kiosk Dynamic QR engine."""

from typing import Optional
import uuid
from pydantic import BaseModel, Field


class KioskAuthRequest(BaseModel):
    """Payload to authenticate a laptop screen kiosk using its office API key."""
    kiosk_api_key: str = Field(..., description="Secret API key assigned to the office kiosk laptop")


class DynamicQRPayload(BaseModel):
    """Payload structure encoded into the dynamic QR code."""
    t_id: str = Field(..., description="Tenant UUID")
    o_id: str = Field(..., description="Office UUID")
    ts: int = Field(..., description="Timestamp of generation (Unix epoch)")
    nonce: str = Field(..., description="Random single-use 16-byte nonce")
    sig: str = Field(..., description="HMAC-SHA256 signature")
    ttl: int = Field(default=15, description="Validity period in seconds")


class KioskQRStreamMessage(BaseModel):
    """Message sent over WebSocket or polling endpoint to the laptop kiosk display."""
    type: str = Field(default="QR_REFRESH")
    office_name: str
    tenant_name: str
    data: DynamicQRPayload
    server_time: str
