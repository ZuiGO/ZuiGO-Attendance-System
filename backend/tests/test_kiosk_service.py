"""Unit and integration tests for Dynamic QR generation and single-use nonce consumption."""

import asyncio
import pytest
from app.services.qr_service import DynamicQRService


@pytest.mark.asyncio
async def test_dynamic_qr_service_generation():
    """Verify QR service generates valid 15-second dynamic QR token."""
    service = DynamicQRService()
    tenant_id = "tenant-test-uuid"
    office_id = "office-test-uuid"

    qr = await service.generate_qr_for_office(tenant_id, office_id)

    assert qr.t_id == tenant_id
    assert qr.o_id == office_id
    assert qr.ttl == 15
    assert len(qr.nonce) == 32
    assert len(qr.sig) == 64


@pytest.mark.asyncio
async def test_dynamic_qr_single_use_consumption():
    """
    CRITICAL ANTI-PROXY TEST:
    Verify that once a QR code nonce is consumed, subsequent attempts with the same token FAIL.
    """
    service = DynamicQRService()
    tenant_id = "tenant-anti-proxy"
    office_id = "office-main"

    qr = await service.generate_qr_for_office(tenant_id, office_id)

    # First consumption: Must succeed
    is_valid, error = await service.consume_nonce(
        tenant_id=qr.t_id,
        office_id=qr.o_id,
        nonce=qr.nonce,
        timestamp=qr.ts,
        signature=qr.sig,
    )
    assert is_valid is True
    assert error is None

    # Second consumption attempt (e.g. friend trying to use the same QR code): MUST BE REJECTED
    is_valid_second, error_second = await service.consume_nonce(
        tenant_id=qr.t_id,
        office_id=qr.o_id,
        nonce=qr.nonce,
        timestamp=qr.ts,
        signature=qr.sig,
    )
    assert is_valid_second is False
    assert error_second == "QR_NONCE_EXPIRED_OR_ALREADY_USED"


@pytest.mark.asyncio
async def test_dynamic_qr_wrong_office_mismatch():
    """Verify that a QR code generated for Office A cannot be submitted for Office B."""
    service = DynamicQRService()
    tenant_id = "tenant-001"
    office_a = "office-A"
    office_b = "office-B"

    qr = await service.generate_qr_for_office(tenant_id, office_a)

    is_valid, error = await service.consume_nonce(
        tenant_id=tenant_id,
        office_id=office_b,  # Tampered office
        nonce=qr.nonce,
        timestamp=qr.ts,
        signature=qr.sig,
    )
    assert is_valid is False
    assert error == "INVALID_SIGNATURE"
