"""Pydantic schemas for authentication and device binding enrollment."""

from typing import List, Optional
import uuid
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Employee login request."""
    email: str
    password: str
    tenant_id: Optional[str] = None


class EnrollDeviceRequest(BaseModel):
    """1:1 Hardware Device Binding Request (KeyStore / Secure Enclave Enrollment)."""
    email: str
    password: str
    device_id: str = Field(..., description="Unique hardware UUID of the smartphone")
    device_public_key: str = Field(..., description="Public key generated in Secure Enclave (PEM format)")
    device_model: Optional[str] = Field(None, description="e.g. iPhone 15 Pro, Pixel 8")


class EnrollFaceRequest(BaseModel):
    """Baseline facial embedding registration during HR onboarding."""
    employee_id: uuid.UUID
    face_embedding: List[float] = Field(..., description="128 or 512-dimensional facial embedding vector")
    photo_url: Optional[str] = None


class TokenResponse(BaseModel):
    """JWT response payload."""
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    employee_id: str
    employee_name: str
    role: str
    tenant_id: str
