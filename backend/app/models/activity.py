"""SQLAlchemy ORM model for User Activity Logs and Audit Trails."""

from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )

    activity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # CLOCK_IN, CLOCK_OUT, TASK_START, TASK_STOP, FIELD_VISIT_ARRIVAL, FIELD_VISIT_OTP_VERIFIED, etc.

    description: Mapped[str] = mapped_column(Text, nullable=False)
    network_type: Mapped[str] = mapped_column(
        String(30), default="OFFICE_WIFI", nullable=False
    )  # OFFICE_WIFI, PERSONAL_CELLULAR, EXTERNAL_WIFI
    is_office_wifi: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id])
