"""Unit tests for security utilities: JWT, bcrypt, and Dynamic QR verification."""

import time
import pytest
from app.core.security import (
    create_access_token,
    decode_token,
    generate_dynamic_qr_payload,
    hash_password,
    verify_dynamic_qr_signature,
    verify_password,
)


def test_password_hashing():
    """Test bcrypt hashing and verification."""
    password = "SecurePassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_access_token():
    """Test JWT creation, claim structure, and decoding."""
    token = create_access_token(
        subject="emp-123",
        tenant_id="tenant-abc",
        role="EMPLOYEE",
        extra_claims={"office_id": "office-xyz"},
    )
    payload = decode_token(token)
    assert payload["sub"] == "emp-123"
    assert payload["tenant_id"] == "tenant-abc"
    assert payload["role"] == "EMPLOYEE"
    assert payload["office_id"] == "office-xyz"
    assert "exp" in payload


def test_dynamic_qr_payload_generation():
    """Test that dynamic QR payload contains all expected cryptographic fields."""
    tenant_id = "tenant-001"
    office_id = "office-001"
    payload, nonce = generate_dynamic_qr_payload(tenant_id, office_id)

    assert payload["t_id"] == tenant_id
    assert payload["o_id"] == office_id
    assert payload["nonce"] == nonce
    assert payload["ttl"] == 15
    assert len(payload["sig"]) == 64  # SHA256 hex string length


def test_dynamic_qr_valid_signature():
    """Test verification of a freshly generated dynamic QR."""
    tenant_id = "tenant-001"
    office_id = "office-001"
    payload, nonce = generate_dynamic_qr_payload(tenant_id, office_id)

    is_valid, error = verify_dynamic_qr_signature(
        tenant_id=payload["t_id"],
        office_id=payload["o_id"],
        timestamp=payload["ts"],
        nonce=payload["nonce"],
        provided_signature=payload["sig"],
        max_skew_seconds=5,
    )
    assert is_valid is True
    assert error is None


def test_dynamic_qr_tampered_signature():
    """Test that tampered signatures are rejected."""
    tenant_id = "tenant-001"
    office_id = "office-001"
    payload, nonce = generate_dynamic_qr_payload(tenant_id, office_id)

    is_valid, error = verify_dynamic_qr_signature(
        tenant_id=payload["t_id"],
        office_id=payload["o_id"],
        timestamp=payload["ts"],
        nonce=payload["nonce"],
        provided_signature="tampered_hex_signature_" + "0" * 42,
    )
    assert is_valid is False
    assert error == "INVALID_SIGNATURE"


def test_dynamic_qr_expired():
    """Test that QR codes older than TTL + skew are rejected."""
    tenant_id = "tenant-001"
    office_id = "office-001"
    payload, nonce = generate_dynamic_qr_payload(tenant_id, office_id)

    # Artificially set timestamp 30 seconds in the past
    stale_timestamp = payload["ts"] - 30

    is_valid, error = verify_dynamic_qr_signature(
        tenant_id=payload["t_id"],
        office_id=payload["o_id"],
        timestamp=stale_timestamp,
        nonce=payload["nonce"],
        provided_signature=payload["sig"],
        max_skew_seconds=5,
    )
    assert is_valid is False
    assert "QR_EXPIRED" in error
