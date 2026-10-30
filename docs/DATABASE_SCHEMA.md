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
        "allowed_clock_skew_seconds": 5
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
```
