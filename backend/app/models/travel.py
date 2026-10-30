"""SQLAlchemy ORM models for Vehicles, Travel Logs, Legs, and Expense Receipts."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.core.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "registration_number", name="uq_vehicle_tenant_reg"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    ownership_type: Mapped[str] = mapped_column(
        String(20), default="COMPANY", nullable=False
    )  # COMPANY, PERSONAL
    vehicle_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # CAR, TWO_WHEELER, VAN, TRUCK
    registration_number: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    make_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fuel_type: Mapped[str] = mapped_column(String(20), default="PETROL", nullable=False)
    assigned_employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
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


class TravelLog(Base):
    __tablename__ = "travel_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    itinerary_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("field_itineraries.id", ondelete="SET NULL"), nullable=True
    )
    vehicle_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True
    )

    transport_mode: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # COMPANY_CAR, PERSONAL_CAR, TWO_WHEELER, CAB, PUBLIC_TRANSPORT, WALKING

    shift_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    shift_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Odometer Readings
    odometer_start_km: Mapped[Optional[float]] = mapped_column(Numeric(10, 1), nullable=True)
    odometer_start_photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    odometer_end_km: Mapped[Optional[float]] = mapped_column(Numeric(10, 1), nullable=True)
    odometer_end_photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # GPS Computed Distance
    gps_total_distance_km: Mapped[float] = mapped_column(Numeric(8, 2), default=0.00, nullable=False)
    distance_discrepancy_pct: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    is_discrepancy_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Reimbursement
    reimbursement_rate_per_km: Mapped[float] = mapped_column(Numeric(6, 2), default=0.00, nullable=False)
    reimbursement_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    reimbursement_status: Mapped[str] = mapped_column(
        String(20), default="PENDING", nullable=False
    )  # PENDING, APPROVED, REJECTED, PAID

    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, COMPLETED, CANCELLED
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
    legs: Mapped[List["TravelLeg"]] = relationship("TravelLeg", back_populates="travel_log", cascade="all, delete-orphan")
    receipts: Mapped[List["TravelExpenseReceipt"]] = relationship("TravelExpenseReceipt", back_populates="travel_log", cascade="all, delete-orphan")


class TravelLeg(Base):
    __tablename__ = "travel_legs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    travel_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("travel_logs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    leg_sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    from_location_name: Mapped[str] = mapped_column(String(255), nullable=False)
    from_coordinates = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    to_location_name: Mapped[str] = mapped_column(String(255), nullable=False)
    to_coordinates = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)

    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    arrival_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    gps_distance_km: Mapped[float] = mapped_column(Numeric(8, 2), default=0.00, nullable=False)
    straight_line_distance_km: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)

    detected_transport_mode: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    avg_speed_kmh: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    max_speed_kmh: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)

    has_unauthorized_stop: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    unauthorized_stop_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    route_deviation_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    travel_log: Mapped["TravelLog"] = relationship("TravelLog", back_populates="legs")


class TravelExpenseReceipt(Base):
    __tablename__ = "travel_expense_receipts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    travel_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("travel_logs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    receipt_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # CAB_RECEIPT, BUS_TICKET, TRAIN_TICKET, METRO_PASS, TOLL_RECEIPT, FUEL_RECEIPT
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    receipt_photo_url: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    travel_log: Mapped["TravelLog"] = relationship("TravelLog", back_populates="receipts")
