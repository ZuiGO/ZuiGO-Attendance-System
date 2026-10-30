# ZuiGO Attendance System — Database Schema & DDL Specification

Target Database: **PostgreSQL 16+** with **PostGIS** and **pgcrypto** extensions.

---

## 1. Schema Extensions & Prerequisites

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "postgis";
```

---

## 2. Table Definitions

### 2.1 Organizations & Branches (Tenancy)

```sql
-- 1. Tenants (Organizations)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(63) UNIQUE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    configuration JSONB NOT NULL DEFAULT '{
        "grace_period_minutes": 15,
        "half_day_threshold_hours": 4.5,
        "full_day_threshold_hours": 8.0,
        "require_face_liveness": true,
        "require_dynamic_qr": true,
        "require_wifi_bssid": true,
        "allowed_clock_skew_seconds": 5,
        "field_visit_default_dwell_minutes": 30,
        "field_visit_require_client_otp": true,
        "field_visit_otp_channel": "SMS"
    }',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Offices (Physical Locations per Tenant)
CREATE TABLE offices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    address TEXT,
    coordinates GEOMETRY(Point, 4326) NOT NULL, -- WGS84 Lat/Long Point
    allowed_radius_meters INT NOT NULL DEFAULT 50,
    allowed_bssid_list TEXT[] NOT NULL DEFAULT '{}', -- Authorized Wi-Fi MACs
    allowed_ip_list INET[] NOT NULL DEFAULT '{}',   -- Corporate public egress IPs
    kiosk_api_key VARCHAR(128) UNIQUE,             -- Authentication key for Laptop Kiosk display
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_offices_tenant ON offices(tenant_id);
CREATE INDEX idx_offices_spatial ON offices USING GIST (coordinates);
```

### 2.2 Employee & Device Management

```sql
-- 3. Departments
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, name)
);

-- 4. Employees
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    office_id UUID REFERENCES offices(id) ON DELETE SET NULL,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    employee_code VARCHAR(50) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(30),
    role VARCHAR(50) NOT NULL DEFAULT 'EMPLOYEE', -- 'ADMIN', 'MANAGER', 'EMPLOYEE'
    manager_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    
    -- Anti-Spoofing & Device Binding Fields
    registered_device_id VARCHAR(255) UNIQUE,     -- Hardware UUID of bound phone
    device_public_key TEXT,                       -- Hardware Keystore Public Key (PEM)
    face_embedding_vector REAL[],                 -- 128-dimensional embedding from baseline photo
    baseline_face_photo_url TEXT,                 -- Secure S3/GCS URL for reference
    device_enrolled_at TIMESTAMPTZ,
    
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, employee_code),
    UNIQUE (tenant_id, email)
);

CREATE INDEX idx_employees_tenant ON employees(tenant_id);
CREATE INDEX idx_employees_role ON employees(tenant_id, role);
CREATE INDEX idx_employees_device ON employees(registered_device_id);
```

### 2.3 Attendance Logging (Presence & Anti-Proxy Audit)

```sql
-- 5. Attendance Records
CREATE TABLE attendance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    office_id UUID NOT NULL REFERENCES offices(id),
    
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    clock_in TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    clock_out TIMESTAMPTZ,
    
    -- Anti-Proxy Verification Audit Details
    clock_in_verification_method VARCHAR(50) NOT NULL DEFAULT 'DYNAMIC_QR_FACE_WIFI',
    clock_in_location GEOMETRY(Point, 4326) NOT NULL,
    clock_in_bssid VARCHAR(50) NOT NULL,
    clock_in_client_ip INET NOT NULL,
    clock_in_device_id VARCHAR(255) NOT NULL,
    clock_in_face_similarity_score NUMERIC(5, 4), -- e.g. 0.9421
    
    -- Clock-out Audit Details
    clock_out_location GEOMETRY(Point, 4326),
    clock_out_verification_method VARCHAR(50),
    
    -- Derived Durations & Status
    gross_duration_seconds INT GENERATED ALWAYS AS (
        CASE WHEN clock_out IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (clock_out - clock_in))::INT 
        ELSE NULL END
    ) STORED,
    
    status VARCHAR(30) NOT NULL DEFAULT 'PRESENT', -- 'PRESENT', 'LATE', 'HALF_DAY', 'OVERTIME'
    is_manual_override BOOLEAN NOT NULL DEFAULT FALSE,
    override_reason TEXT,
    overridden_by UUID REFERENCES employees(id),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, employee_id, date)
);

CREATE INDEX idx_attendance_tenant_date ON attendance_records(tenant_id, date);
CREATE INDEX idx_attendance_employee_date ON attendance_records(employee_id, date);
```

### 2.4 Projects, Tasks & Time Tracking

```sql
-- 6. Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    code VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, name)
);

-- 7. Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    assigned_to UUID REFERENCES employees(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'TODO', -- 'TODO', 'IN_PROGRESS', 'BLOCKED', 'DONE'
    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM', -- 'LOW', 'MEDIUM', 'HIGH', 'URGENT'
    estimated_hours NUMERIC(6, 2),
    due_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tasks_assigned ON tasks(tenant_id, assigned_to, status);
CREATE INDEX idx_tasks_project ON tasks(tenant_id, project_id);

-- 8. Task Time Entries (Granular Task Stopwatch & Logs)
CREATE TABLE task_time_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    attendance_id UUID REFERENCES attendance_records(id) ON DELETE CASCADE,
    
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_seconds INT GENERATED ALWAYS AS (
        CASE WHEN end_time IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (end_time - start_time))::INT 
        ELSE NULL END
    ) STORED,
    
    is_billable BOOLEAN NOT NULL DEFAULT TRUE,
    notes TEXT,
    source VARCHAR(30) NOT NULL DEFAULT 'MOBILE_STOPWATCH', -- 'MOBILE_STOPWATCH', 'MANUAL_ENTRY'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_time_entries_employee_time ON task_time_entries(tenant_id, employee_id, start_time);
CREATE INDEX idx_time_entries_task ON task_time_entries(tenant_id, task_id);
```

### 2.5 Field-Visit & Route Tracking (Proof of Physical Visit - PoPV)

```sql
-- 9. Client Destinations (Hospitals, Dealers, Distributors, Customers)
CREATE TABLE client_destinations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    client_type VARCHAR(50) NOT NULL DEFAULT 'CUSTOMER', -- 'HOSPITAL', 'DEALER', 'DISTRIBUTOR', 'CUSTOMER'
    contact_person VARCHAR(150),
    contact_phone VARCHAR(30),
    otp_channel VARCHAR(20) NOT NULL DEFAULT 'SMS', -- 'SMS', 'WHATSAPP', 'BOTH'
    address TEXT,
    coordinates GEOMETRY(Point, 4326) NOT NULL,
    geofence_radius_meters INT NOT NULL DEFAULT 75,
    min_dwell_minutes INT NOT NULL DEFAULT 30, -- Default 30 mins, overridden by tenant config
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_destinations_tenant ON client_destinations(tenant_id);
CREATE INDEX idx_destinations_spatial ON client_destinations USING GIST (coordinates);

-- 10. Field Itineraries (Daily Beat / Route Plan)
CREATE TABLE field_itineraries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES employees(id),
    title VARCHAR(200) NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(30) NOT NULL DEFAULT 'PLANNED', -- 'PLANNED', 'IN_PROGRESS', 'COMPLETED', 'PARTIAL'
    total_planned_stops INT NOT NULL DEFAULT 0,
    total_completed_stops INT NOT NULL DEFAULT 0,
    total_travel_distance_km NUMERIC(8, 2) DEFAULT 0.00,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_itineraries_employee_date ON field_itineraries(tenant_id, employee_id, date);

-- 11. Field Visit Stops (Individual Stops on Route)
CREATE TABLE field_visit_stops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    itinerary_id UUID NOT NULL REFERENCES field_itineraries(id) ON DELETE CASCADE,
    destination_id UUID NOT NULL REFERENCES client_destinations(id) ON DELETE CASCADE,
    sequence_order INT NOT NULL DEFAULT 1,
    planned_time TIMESTAMPTZ,
    
    -- Verification Timestamps & Metrics
    actual_arrival_time TIMESTAMPTZ,
    actual_departure_time TIMESTAMPTZ,
    dwell_time_seconds INT GENERATED ALWAYS AS (
        CASE WHEN actual_departure_time IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (actual_departure_time - actual_arrival_time))::INT 
        ELSE NULL END
    ) STORED,
    
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'ARRIVED', 'COMPLETED', 'SKIPPED', 'CANCELLED'
    
    -- Presence Verification
    check_in_location GEOMETRY(Point, 4326),
    check_in_distance_meters NUMERIC(8, 2), -- Distance from target coordinates upon check-in
    check_out_location GEOMETRY(Point, 4326),
    is_geofence_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_dwell_time_satisfied BOOLEAN NOT NULL DEFAULT FALSE,
    
    skip_reason TEXT,
    meeting_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_visit_stops_itinerary ON field_visit_stops(itinerary_id, sequence_order);

-- 12. Field Visit Proofs (Tamper-Proof Audit Artifacts)
CREATE TABLE field_visit_proofs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    visit_stop_id UUID NOT NULL REFERENCES field_visit_stops(id) ON DELETE CASCADE,
    proof_type VARCHAR(50) NOT NULL, -- 'LIVE_CAMERA_PHOTO', 'CLIENT_SMS_OTP', 'CLIENT_WHATSAPP_OTP'
    file_url TEXT NOT NULL,
    captured_coordinates GEOMETRY(Point, 4326) NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}' -- Includes EXIF verification, signer name, etc.
);

CREATE INDEX idx_visit_proofs_stop ON field_visit_proofs(visit_stop_id);

-- 13. Client OTP Verification Log
CREATE TABLE client_otp_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    visit_stop_id UUID NOT NULL REFERENCES field_visit_stops(id) ON DELETE CASCADE,
    destination_id UUID NOT NULL REFERENCES client_destinations(id) ON DELETE CASCADE,
    recipient_phone VARCHAR(30) NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    channel VARCHAR(20) NOT NULL DEFAULT 'SMS', -- 'SMS', 'WHATSAPP'
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    verified_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL,
    attempts INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 3,
    status VARCHAR(20) NOT NULL DEFAULT 'SENT', -- 'SENT', 'VERIFIED', 'EXPIRED', 'FAILED'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_otp_verifications_stop ON client_otp_verifications(visit_stop_id);

-- 14. Location Breadcrumbs (Continuous Route & Mileage Telemetry)
CREATE TABLE location_breadcrumbs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    itinerary_id UUID REFERENCES field_itineraries(id) ON DELETE SET NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    coordinates GEOMETRY(Point, 4326) NOT NULL,
    accuracy_meters NUMERIC(6, 2),
    speed_kmh NUMERIC(6, 2),
    battery_level INT,
    is_mock BOOLEAN NOT NULL DEFAULT FALSE,
    activity_type VARCHAR(30) DEFAULT 'UNKNOWN', -- 'STATIONARY', 'IN_VEHICLE', 'WALKING'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_breadcrumbs_emp_time ON location_breadcrumbs(tenant_id, employee_id, recorded_at);
CREATE INDEX idx_breadcrumbs_spatial ON location_breadcrumbs USING GIST (coordinates);
```

---

## 3. Row-Level Security (RLS) Setup

```sql
-- Enable Row Level Security on all tenant tables
ALTER TABLE offices ENABLE ROW LEVEL SECURITY;
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_time_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_destinations ENABLE ROW LEVEL SECURITY;
ALTER TABLE field_itineraries ENABLE ROW LEVEL SECURITY;
ALTER TABLE field_visit_stops ENABLE ROW LEVEL SECURITY;
ALTER TABLE field_visit_proofs ENABLE ROW LEVEL SECURITY;
ALTER TABLE location_breadcrumbs ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_otp_verifications ENABLE ROW LEVEL SECURITY;

-- Create Tenant Isolation Policies
CREATE POLICY tenant_isolation_offices ON offices
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY tenant_isolation_departments ON departments
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY tenant_isolation_employees ON employees
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY tenant_isolation_attendance ON attendance_records
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY tenant_isolation_projects ON projects
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY tenant_isolation_tasks ON tasks
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY tenant_isolation_time_entries ON task_time_entries
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY tenant_isolation_destinations ON client_destinations
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY tenant_isolation_itineraries ON field_itineraries
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY tenant_isolation_stops ON field_visit_stops
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY tenant_isolation_proofs ON field_visit_proofs
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY tenant_isolation_breadcrumbs ON location_breadcrumbs
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY tenant_isolation_otp ON client_otp_verifications
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
```
