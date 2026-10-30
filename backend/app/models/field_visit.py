"""SQLAlchemy ORM models for Field Visits, Destinations, and Client OTP Verifications."""

from datetime import date, datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.core.database import Base


class ClientDestination(Base):
    __tablename__ = "client_destinations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_type: Mapped[str] = mapped_column(
        String(50), default="CUSTOMER", nullable=False
    )  # HOSPITAL, DEALER, DISTRIBUTOR, CUSTOMER
    contact_person: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    otp_channel: Mapped[str] = mapped_column(String(20), default="SMS", nullable=False)  # SMS, WHATSAPP, BOTH
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    coordinates = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    geofence_radius_meters: Mapped[int] = mapped_column(Integer, default=75, nullable=False)
    min_dwell_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
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
    visit_stops: Mapped[List["FieldVisitStop"]] = relationship("FieldVisitStop", back_populates="destination")


class FieldItinerary(Base):
    __tablename__ = "field_itineraries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(30), default="PLANNED", nullable=False
    )  # PLANNED, IN_PROGRESS, COMPLETED, PARTIAL
    total_planned_stops: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_completed_stops: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_travel_distance_km: Mapped[float] = mapped_column(Numeric(8, 2), default=0.00, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    stops: Mapped[List["FieldVisitStop"]] = relationship("FieldVisitStop", back_populates="itinerary", cascade="all, delete-orphan")


class FieldVisitStop(Base):
    __tablename__ = "field_visit_stops"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    itinerary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("field_itineraries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    destination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_destinations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    planned_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    actual_arrival_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_departure_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(
        String(30), default="PENDING", nullable=False
    )  # PENDING, ARRIVED, COMPLETED, SKIPPED, CANCELLED

    check_in_location = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    check_in_distance_meters: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    check_out_location = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    is_geofence_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_dwell_time_satisfied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    skip_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meeting_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    itinerary: Mapped["FieldItinerary"] = relationship("FieldItinerary", back_populates="stops")
    destination: Mapped["ClientDestination"] = relationship("ClientDestination", back_populates="visit_stops")
    proofs: Mapped[List["FieldVisitProof"]] = relationship("FieldVisitProof", back_populates="stop", cascade="all, delete-orphan")
    otp_verifications: Mapped[List["ClientOtpVerification"]] = relationship("ClientOtpVerification", back_populates="stop", cascade="all, delete-orphan")


class FieldVisitProof(Base):
    __tablename__ = "field_visit_proofs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    visit_stop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("field_visit_stops.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proof_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # LIVE_CAMERA_PHOTO, CLIENT_SMS_OTP, CLIENT_WHATSAPP_OTP
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    captured_coordinates = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Relationships
    stop: Mapped["FieldVisitStop"] = relationship("FieldVisitStop", back_populates="proofs")


class ClientOtpVerification(Base):
    __tablename__ = "client_otp_verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    visit_stop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("field_visit_stops.id", ondelete="CASCADE"), nullable=False, index=True
    )
    destination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_destinations.id", ondelete="CASCADE"), nullable=False
    )
    recipient_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    otp_code: Mapped[str] = mapped_column(String(6), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="SMS", nullable=False)  # SMS, WHATSAPP
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="SENT", nullable=False)  # SENT, VERIFIED, EXPIRED, FAILED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    stop: Mapped["FieldVisitStop"] = relationship("FieldVisitStop", back_populates="otp_verifications")
