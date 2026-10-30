"""SQLAlchemy ORM models for Location Breadcrumbs and Telemetry."""

from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from app.core.database import Base


class LocationBreadcrumb(Base):
    __tablename__ = "location_breadcrumbs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    itinerary_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("field_itineraries.id", ondelete="SET NULL"), nullable=True
    )

    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    coordinates = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    accuracy_meters: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    speed_kmh: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    battery_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    activity_type: Mapped[str] = mapped_column(
        String(30), default="UNKNOWN", nullable=False
    )  # STATIONARY, IN_VEHICLE, WALKING, ON_BICYCLE, RUNNING

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
