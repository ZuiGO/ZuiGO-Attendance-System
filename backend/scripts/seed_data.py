"""One-Click Comprehensive Database Seeder for ZuiGO Attendance System.

Seeds realistic multi-tenant demo data:
- Tenant: ZuiGO Technologies (subdomain: zuigo)
- Cyber City HQ Office with WGS84 PostGIS point, geofence, and authorized Wi-Fi BSSID
- Departments & Employees (Admin, Field Engineers, Managers)
- Client Destinations (Hospitals, Pharma Distributors, Diagnostic Labs)
- Fleet Vehicles (Company Car, Personal Bikes & Cars)
- Projects and Tasks
- Active Field Itineraries with Proofs & OTP Verifications
- Travel Logs with Mileage Discrepancy & Anti-Fraud Alerts
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
import logging
import os
import sys
import uuid

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from geoalchemy2.elements import WKTElement

from app.core.database import AsyncSessionLocal, engine
from app.core.security import hash_password
from app.models.tenant import Tenant, Office
from app.models.employee import Department, Employee
from app.models.attendance import AttendanceRecord
from app.models.task import Project, Task, TaskTimeEntry
from app.models.field_visit import (
    ClientDestination,
    FieldItinerary,
    FieldVisitStop,
    FieldVisitProof,
    ClientOtpVerification,
)
from app.models.travel import Vehicle, TravelLog, TravelLeg

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_data")


async def seed():
    logger.info("Starting ZuiGO Demo Database Seeding...")

    async with AsyncSessionLocal() as session:
        # 1. Check if tenant already exists
        result = await session.execute(select(Tenant).where(Tenant.subdomain == "zuigo"))
        existing_tenant = result.scalar_one_or_none()

        if existing_tenant:
            logger.info("ℹ️ Tenant 'zuigo' already exists in database (ID: %s).", existing_tenant.id)
            tenant_id = existing_tenant.id
        else:
            logger.info("Creating Tenant 'ZuiGO Technologies'...")
            tenant = Tenant(
                id=uuid.uuid4(),
                name="ZuiGO Technologies Inc.",
                subdomain="zuigo",
                is_active=True,
                configuration={
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
            session.add(tenant)
            await session.flush()
            tenant_id = tenant.id
            logger.info("Created Tenant ID: %s", tenant_id)

        # 2. HQ Office
        office_res = await session.execute(
            select(Office).where(Office.tenant_id == tenant_id, Office.name == "Cyber City HQ")
        )
        office = office_res.scalar_one_or_none()
        if not office:
            logger.info("Creating Cyber City HQ Office...")
            office = Office(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                name="Cyber City HQ",
                address="DLF Cyber City, Building 10, Tower B, Gurugram, Haryana 122002",
                coordinates=WKTElement("POINT(77.0878 28.4986)", srid=4326),
                allowed_radius_meters=50,
                allowed_bssid_list=["3c:37:12:89:af:90", "e8:48:b8:c1:02:44"],
                allowed_ip_list=["203.0.113.195"],
                kiosk_api_key="kiosk_hq_dev_key_2026",
                is_active=True,
            )
            session.add(office)
            await session.flush()

        # 3. Departments
        dept_names = ["Field Operations", "Engineering", "Hospital Relations"]
        depts = {}
        for d_name in dept_names:
            d_res = await session.execute(
                select(Department).where(Department.tenant_id == tenant_id, Department.name == d_name)
            )
            d = d_res.scalar_one_or_none()
            if not d:
                d = Department(id=uuid.uuid4(), tenant_id=tenant_id, name=d_name)
                session.add(d)
                await session.flush()
            depts[d_name] = d

        # 4. Employees
        pw_hash = hash_password("password123")
        employees_data = [
            {
                "code": "EMP-001",
                "name": "Jayesh Admin",
                "email": "jayesh@zuigo.ai",
                "role": "ADMIN",
                "dept": "Engineering",
                "phone": "+919800000001",
                "device": None,
            },
            {
                "code": "EMP-1001",
                "name": "Alex Johnson",
                "email": "alex.j@zuigo.ai",
                "role": "EMPLOYEE",
                "dept": "Field Operations",
                "phone": "+919800001001",
                "device": "DEV-PIXEL-7-PRO-SECURE",
            },
            {
                "code": "EMP-1002",
                "name": "Priya Sharma",
                "email": "priya.s@zuigo.ai",
                "role": "EMPLOYEE",
                "dept": "Hospital Relations",
                "phone": "+919800001002",
                "device": "DEV-SAMSUNG-S23-ULTRA",
            },
            {
                "code": "EMP-1003",
                "name": "Rahul Verma",
                "email": "rahul.v@zuigo.ai",
                "role": "MANAGER",
                "dept": "Field Operations",
                "phone": "+919800001003",
                "device": "DEV-IPHONE-15-PRO-MAX",
            },
        ]

        employees = {}
        for ed in employees_data:
            e_res = await session.execute(
                select(Employee).where(Employee.tenant_id == tenant_id, Employee.employee_code == ed["code"])
            )
            emp = e_res.scalar_one_or_none()
            if not emp:
                emp = Employee(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    office_id=office.id,
                    department_id=depts[ed["dept"]].id,
                    employee_code=ed["code"],
                    full_name=ed["name"],
                    email=ed["email"],
                    hashed_password=pw_hash,
                    phone=ed["phone"],
                    role=ed["role"],
                    registered_device_id=ed["device"],
                    is_active=True,
                )
                session.add(emp)
                await session.flush()
                logger.info("Created Employee: %s (%s)", ed["name"], ed["code"])
            employees[ed["code"]] = emp

        # 5. Client Destinations (Field Visits)
        destinations_data = [
            {
                "name": "Apollo City Hospital",
                "type": "HOSPITAL",
                "contact": "Dr. K. Mehta",
                "phone": "+919876543210",
                "otp_channel": "SMS",
                "point": "POINT(77.2612 28.5355)",
                "dwell": 30,
                "radius": 75,
            },
            {
                "name": "Metro Pharma Distributors",
                "type": "DISTRIBUTOR",
                "contact": "Sunil Gupta",
                "phone": "+919812345678",
                "otp_channel": "WHATSAPP",
                "point": "POINT(77.2090 28.5120)",
                "dwell": 30,
                "radius": 75,
            },
            {
                "name": "LifeCare Diagnostics Hub",
                "type": "CUSTOMER",
                "contact": "Dr. Ananya Ray",
                "phone": "+919922334455",
                "otp_channel": "BOTH",
                "point": "POINT(77.0710 28.4720)",
                "dwell": 45,
                "radius": 80,
            },
            {
                "name": "Fortis Regional Medical Center",
                "type": "HOSPITAL",
                "contact": "Rajiv Saxena",
                "phone": "+919811122233",
                "otp_channel": "SMS",
                "point": "POINT(77.0726 28.4601)",
                "dwell": 30,
                "radius": 75,
            },
        ]

        destinations = {}
        for dd in destinations_data:
            dest_res = await session.execute(
                select(ClientDestination).where(
                    ClientDestination.tenant_id == tenant_id, ClientDestination.name == dd["name"]
                )
            )
            dest = dest_res.scalar_one_or_none()
            if not dest:
                dest = ClientDestination(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    name=dd["name"],
                    client_type=dd["type"],
                    contact_person=dd["contact"],
                    contact_phone=dd["phone"],
                    otp_channel=dd["otp_channel"],
                    coordinates=WKTElement(dd["point"], srid=4326),
                    geofence_radius_meters=dd["radius"],
                    min_dwell_minutes=dd["dwell"],
                    is_active=True,
                )
                session.add(dest)
                await session.flush()
                logger.info("Created Client Destination: %s (Dwell: %d min)", dd["name"], dd["dwell"])
            destinations[dd["name"]] = dest

        # 6. Fleet Vehicles
        vehicles_data = [
            {
                "reg": "DL-01-AB-1234",
                "type": "CAR",
                "ownership": "COMPANY",
                "model": "Toyota Innova Crysta",
                "fuel": "DIESEL",
                "emp": "EMP-1001",
            },
            {
                "reg": "HR-26-DQ-5678",
                "type": "TWO_WHEELER",
                "ownership": "PERSONAL",
                "model": "Bajaj Pulsar 150",
                "fuel": "PETROL",
                "emp": "EMP-1002",
            },
            {
                "reg": "DL-09-XY-9999",
                "type": "CAR",
                "ownership": "PERSONAL",
                "model": "Hyundai Creta",
                "fuel": "PETROL",
                "emp": "EMP-1003",
            },
        ]

        vehicles = {}
        for vd in vehicles_data:
            veh_res = await session.execute(
                select(Vehicle).where(
                    Vehicle.tenant_id == tenant_id, Vehicle.registration_number == vd["reg"]
                )
            )
            veh = veh_res.scalar_one_or_none()
            if not veh:
                veh = Vehicle(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    ownership_type=vd["ownership"],
                    vehicle_type=vd["type"],
                    registration_number=vd["reg"],
                    make_model=vd["model"],
                    fuel_type=vd["fuel"],
                    assigned_employee_id=employees[vd["emp"]].id,
                    is_active=True,
                )
                session.add(veh)
                await session.flush()
                logger.info("Created Vehicle: %s (%s)", vd["reg"], vd["model"])
            vehicles[vd["reg"]] = veh

        # 7. Projects & Tasks
        proj_res = await session.execute(
            select(Project).where(Project.tenant_id == tenant_id, Project.name == "Hospital Equipment Audit")
        )
        project = proj_res.scalar_one_or_none()
        if not project:
            project = Project(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                name="Hospital Equipment Audit",
                description="Quarterly physical and digital audit of hospital medical devices.",
                code="HEA-2026",
                is_active=True,
            )
            session.add(project)
            await session.flush()

            t1 = Task(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                project_id=project.id,
                name="Biomedical Sensor Calibration",
                code="CAL-01",
                is_active=True,
            )
            t2 = Task(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                project_id=project.id,
                name="Client OTP Signoff & Report",
                code="SGN-02",
                is_active=True,
            )
            session.add_all([t1, t2])
            await session.flush()
            logger.info("Created Project: %s with 2 Tasks", project.name)

        # 8. Sample Travel Logs (Reimbursements & Fraud Discrepancy Alert)
        tl_res = await session.execute(
            select(TravelLog).where(
                TravelLog.tenant_id == tenant_id,
                TravelLog.employee_id == employees["EMP-1001"].id,
            )
        )
        travel_log1 = tl_res.scalar_one_or_none()
        if not travel_log1:
            # Clean Trip
            now = datetime.now(timezone.utc)
            travel_log1 = TravelLog(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                employee_id=employees["EMP-1001"].id,
                vehicle_id=vehicles["DL-01-AB-1234"].id,
                transport_mode="COMPANY_CAR",
                shift_start_time=now - timedelta(hours=4),
                shift_end_time=now - timedelta(minutes=30),
                odometer_start_km=45210.0,
                odometer_end_km=45238.0,
                gps_total_distance_km=27.4,
                distance_discrepancy_pct=2.19,
                is_discrepancy_flagged=False,
                reimbursement_rate_per_km=8.00,
                reimbursement_amount=224.00,
                reimbursement_status="APPROVED",
                status="COMPLETED",
            )
            session.add(travel_log1)

            # Flagged Trip (> 15% fraud alert)
            travel_log2 = TravelLog(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                employee_id=employees["EMP-1003"].id,
                vehicle_id=vehicles["DL-09-XY-9999"].id,
                transport_mode="PERSONAL_CAR",
                shift_start_time=now - timedelta(hours=3),
                shift_end_time=now - timedelta(minutes=10),
                odometer_start_km=12000.0,
                odometer_end_km=12065.0,
                gps_total_distance_km=42.0,
                distance_discrepancy_pct=54.76,  # 54.8% >> 15% threshold!
                is_discrepancy_flagged=True,
                reimbursement_rate_per_km=8.00,
                reimbursement_amount=520.00,
                reimbursement_status="PENDING",
                status="COMPLETED",
            )
            session.add(travel_log2)
            await session.flush()
            logger.info("Created Sample Travel Shifts (1 Approved, 1 Flagged 54.8% Discrepancy Alert)")

        await session.commit()
        logger.info("🎉 Database Seeding Successfully Completed!")


if __name__ == "__main__":
    asyncio.run(seed())
