"""SQLAlchemy ORM models for Attendance Records."""

from datetime import date, datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.core.database import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "employee_id", "date", name="uq_attendance_tenant_emp_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("offices.id"), nullable=False
    )

    date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    clock_in: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    clock_out: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Anti-Proxy Verification Audit Details
    clock_in_verification_method: Mapped[str] = mapped_column(
        String(50), default="DYNAMIC_QR_FACE_WIFI", nullable=False
    )
    clock_in_location = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    clock_in_bssid: Mapped[str] = mapped_column(String(50), nullable=False)
    clock_in_client_ip: Mapped[str] = mapped_column(INET, nullable=False)
    clock_in_device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    clock_in_face_similarity_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)

    # Clock-out Audit Details
    clock_out_location = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    clock_out_verification_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Attendance Status: PRESENT, LATE, HALF_DAY, OVERTIME
    status: Mapped[str] = mapped_column(String(30), default="PRESENT", nullable=False)
    is_manual_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    overridden_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True
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
