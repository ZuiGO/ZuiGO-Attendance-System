"""Security utilities: JWT, Password Hashing, and Dynamic QR HMAC-SHA256."""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Any, Dict, Optional, Tuple

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hashes a plain text password using bcrypt with automatic salt."""
    salt = bcrypt.gensalt(rounds=12)
    # Truncate password at 72 bytes per bcrypt specification
    hashed = bcrypt.hashpw(password.encode("utf-8")[:72], salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    subject: str,
    tenant_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Generates an encrypted JWT access token scoped to tenant and role."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


# ---------------------------------------------------------------------------
# Dynamic Rotating QR Cryptographic Engine
# ---------------------------------------------------------------------------

def generate_dynamic_qr_payload(
    tenant_id: str,
    office_id: str,
) -> Tuple[Dict[str, Any], str]:
    """
    Generates a cryptographically signed dynamic QR payload and a unique nonce.
    Token validity: 15 seconds.
    Signature: HMAC-SHA256(tenant_id + office_id + timestamp + nonce, SECRET)
    """
    timestamp = int(datetime.now(timezone.utc).timestamp())
    nonce = secrets.token_hex(16)

    message = f"{tenant_id}:{office_id}:{timestamp}:{nonce}".encode("utf-8")
    signature = hmac.new(
        settings.QR_HMAC_SECRET.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()

    payload = {
        "t_id": tenant_id,
        "o_id": office_id,
        "ts": timestamp,
        "nonce": nonce,
        "sig": signature,
        "ttl": settings.QR_CODE_TTL_SECONDS,
    }
    return payload, nonce


def verify_dynamic_qr_signature(
    tenant_id: str,
    office_id: str,
    timestamp: int,
    nonce: str,
    provided_signature: str,
    max_skew_seconds: int = 5,
) -> Tuple[bool, Optional[str]]:
    """
    Validates QR code freshness and HMAC signature.
    Returns (is_valid, error_reason).
    """
    current_time = int(datetime.now(timezone.utc).timestamp())
    age = current_time - timestamp

    # Check for expiration (validity window + allowed clock skew)
    max_allowed_age = settings.QR_CODE_TTL_SECONDS + max_skew_seconds
    if age > max_allowed_age:
        return False, f"QR_EXPIRED (age: {age}s, max allowed: {max_allowed_age}s)"
    if age < -max_skew_seconds:
        return False, "QR_TIMESTAMP_IN_FUTURE"

    # Re-compute HMAC signature
    message = f"{tenant_id}:{office_id}:{timestamp}:{nonce}".encode("utf-8")
    expected_signature = hmac.new(
        settings.QR_HMAC_SECRET.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, provided_signature):
        return False, "INVALID_SIGNATURE"

    return True, None
