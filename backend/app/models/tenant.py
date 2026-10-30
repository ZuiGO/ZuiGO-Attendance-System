"""SQLAlchemy ORM models for Tenants and Offices."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subdomain: Mapped[str] = mapped_column(String(63), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "grace_period_minutes": 15,
            "half_day_threshold_hours": 4.5,
            "full_day_threshold_hours": 8.0,
            "require_face_liveness": True,
            "require_dynamic_qr": True,
            "require_wifi_bssid": True,
            "field_visit_default_dwell_minutes": 30,
            "field_visit_require_client_otp": True,
            "field_visit_otp_channel": "SMS",
            "travel_reimbursement_rates": {
                "PERSONAL_CAR": 8.00,
                "TWO_WHEELER": 4.00,
                "CAB": "ACTUAL",
                "PUBLIC_TRANSPORT": "ACTUAL",
            },
            "odometer_discrepancy_threshold_pct": 15.0,
        },
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    offices: Mapped[List["Office"]] = relationship("Office", back_populates="tenant", cascade="all, delete-orphan")


class Office(Base):
    __tablename__ = "offices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # PostGIS Point Geometry: (longitude, latitude) in WGS84 (SRID 4326)
    coordinates = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    allowed_radius_meters: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    
    # Authorized Wi-Fi BSSIDs (MAC addresses) and Corporate Gateway Public IPs
    allowed_bssid_list: Mapped[List[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    allowed_ip_list: Mapped[List[str]] = mapped_column(ARRAY(INET), default=list, nullable=False)
    
    # Laptop Screen Kiosk API Authentication Key
    kiosk_api_key: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="offices")
