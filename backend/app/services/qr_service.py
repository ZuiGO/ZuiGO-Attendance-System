"""Dynamic Rotating QR Code service with single-use nonce lifecycle in Redis."""

from datetime import datetime, timezone
import json
import time
from typing import Any, Dict, Optional, Tuple

import redis.asyncio as aioredis
from app.core.config import settings
from app.core.security import generate_dynamic_qr_payload, verify_dynamic_qr_signature
from app.schemas.kiosk import DynamicQRPayload

# In-memory fallback cache for test environments where Redis is not running
_in_memory_nonces: Dict[str, Tuple[str, float]] = {}


class DynamicQRService:
    """Service managing 15-second rotating QR generation and single-use atomic consumption."""

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis = redis_client

    async def generate_qr_for_office(
        self,
        tenant_id: str,
        office_id: str,
    ) -> DynamicQRPayload:
        """
        Generates a new dynamic QR token and stores the single-use nonce in Redis with a 20-second TTL.
        """
        payload_dict, nonce = generate_dynamic_qr_payload(
            tenant_id=tenant_id,
            office_id=office_id,
        )

        nonce_key = f"qr_nonce:{nonce}"
        nonce_val = json.dumps({
            "tenant_id": tenant_id,
            "office_id": office_id,
            "timestamp": payload_dict["ts"],
        })
        ttl_seconds = settings.QR_CODE_TTL_SECONDS + settings.QR_SKEW_TOLERANCE_SECONDS

        if self.redis is not None:
            try:
                await self.redis.set(nonce_key, nonce_val, ex=ttl_seconds)
            except Exception:
                # Fallback to in-memory store
                _in_memory_nonces[nonce] = (nonce_val, time.time() + ttl_seconds)
        else:
            _in_memory_nonces[nonce] = (nonce_val, time.time() + ttl_seconds)

        return DynamicQRPayload(**payload_dict)

    async def consume_nonce(
        self,
        tenant_id: str,
        office_id: str,
        nonce: str,
        timestamp: int,
        signature: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Atomically validates and consumes the QR code.
        Guarantees:
          1. Cryptographic HMAC validity.
          2. Freshness within TTL + clock skew.
          3. Single-use: Once consumed, the nonce is deleted. Duplicate scans are blocked.
        """
        # Step 1: Validate HMAC signature and timestamp freshness
        is_valid, error = verify_dynamic_qr_signature(
            tenant_id=tenant_id,
            office_id=office_id,
            timestamp=timestamp,
            nonce=nonce,
            provided_signature=signature,
            max_skew_seconds=settings.QR_SKEW_TOLERANCE_SECONDS,
        )
        if not is_valid:
            return False, error

        # Step 2: Atomic Nonce consumption (Single-Use Defense)
        nonce_key = f"qr_nonce:{nonce}"
        stored_data_str: Optional[str] = None

        if self.redis is not None:
            try:
                # Redis 6.2+ atomic GETDEL
                stored_data_str = await self.redis.getdel(nonce_key)
            except Exception:
                # Fallback if getdel fails or offline
                if nonce in _in_memory_nonces:
                    val, exp = _in_memory_nonces.pop(nonce)
                    if time.time() <= exp:
                        stored_data_str = val
        else:
            if nonce in _in_memory_nonces:
                val, exp = _in_memory_nonces.pop(nonce)
                if time.time() <= exp:
                    stored_data_str = val

        if not stored_data_str:
            return False, "QR_NONCE_EXPIRED_OR_ALREADY_USED"

        try:
            stored_data = json.loads(stored_data_str)
            if stored_data.get("office_id") != office_id or stored_data.get("tenant_id") != tenant_id:
                return False, "QR_OFFICE_TENANT_MISMATCH"
        except Exception:
            return False, "CORRUPT_NONCE_DATA"

        return True, None
