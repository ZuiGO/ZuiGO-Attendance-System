# ZuiGO Attendance & Task Tracking System

An enterprise-grade, multi-tenant physical presence attendance and task tracking platform engineered without dedicated biometric hardware. 

Ensures dependable physical presence using multi-factor zero-trust verification (Dynamic Rotating QR, Hardware Device Binding, On-Device AI Facial Liveness, Office Wi-Fi BSSID validation, and PostGIS Geofencing), combined with real-time task time tracking and employer analytics.

---

## 🏛️ System Architecture Overview

```
                         ┌────────────────────────────────────────────────────────┐
                         │              Laptop / Screen Web Kiosk                 │
                         │    (Displays Dynamic HMAC-SHA256 QR Code every 15s)    │
                         └───────────────────────────┬────────────────────────────┘
                                                     │ Visual Scan
                                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      Employee React Native Mobile Application                   │
│  - Device Keystore / Secure Enclave Binding (1 User : 1 Device)                 │
│  - On-Device AI Face Verification & 3D Liveness Detection                       │
│  - Network Geofence: Wi-Fi BSSID + Public IP + GPS Spoof Detection              │
│  - Integrated Task Stopwatch & Time Logger                                      │
└────────────────────────────────────────────┬────────────────────────────────────┘
                                             │ HTTPS (mTLS / Signed Payload)
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Python FastAPI Backend Service                         │
│  - Multi-Tenant Middleware (Subdomain / Header Tenant Resolution)               │
│  - Dynamic Token Validation & Nonce Invalidation Engine                         │
│  - Attendance Engine (Verification, Shifts, Grace Periods, Overtime)            │
│  - Task & Timesheet Management API                                              │
└───────────────────────┬─────────────────────────────────┬───────────────────────┘
                        │                                 │
                        ▼                                 ▼
         ┌───────────────────────────────┐ ┌──────────────────────────────────────┐
         │       Redis In-Memory         │ │        PostgreSQL 16 + PostGIS       │
         │ - 15-second Nonce Tracking    │ │ - Row-Level Security (RLS) Isolation │
         │ - Rate Limiting & Blacklists  │ │ - PostGIS Spatial Geofence Index     │
         │ - Real-Time Presence Cache    │ │ - Relational ACID Timesheets         │
         │ - Webhook / WebSocket PubSub  │ │ - Configurable JSONB Policy Engine   │
         └───────────────────────────────┘ └──────────────────────────────────────┘
```

---

## 🔒 Multi-Factor Presence Verification (Zero-Trust Model)

To eliminate **buddy punching** and **remote proxy check-ins** without dedicated biometric hardware:

1. **Dynamic Rotating Cryptographic QR (Laptop Screen Kiosk):**
   * The laptop web app connects to FastAPI via WebSocket / SSE.
   * Server generates a signed payload every **15 seconds**: `HMAC_SHA256(tenant_id + office_id + timestamp + nonce, SECRET_KEY)`.
   * Nonces are stored in Redis with an exact 20-second TTL.
   * *Anti-Proxy Protection:* Photos sent to coworkers expire before they can be scanned. Once a nonce is used, it is atomically deleted from Redis (Single-Use Token).

2. **Strict 1:1 Hardware Device Binding:**
   * On initial login, a cryptographic key pair is generated inside the mobile phone's **Apple Secure Enclave** or **Android KeyStore**.
   * Public key & hardware identifier are enrolled in PostgreSQL.
   * *Anti-Proxy Protection:* An employee cannot log into a colleague's account on their phone to check in for them.

3. **Network & Indoor Geofencing:**
   * Employee app captures the active **Wi-Fi BSSID (MAC Address of office router)** and transmits it with the check-in request.
   * Backend verifies that the BSSID matches the tenant office's authorized list and the request comes from the office gateway IP.
   * *Anti-Proxy Protection:* Defeats GPS spoofing; radio Wi-Fi signals cannot be received from outside office walls.

4. **On-Device Facial Verification & Anti-Spoofing Liveness:**
   * Employs on-device Google ML Kit / Apple Vision to detect micro-movements (blinking/nodding/texture depth).
   * Generates a 128-dimensional facial embedding and compares it against the employee's baseline photo.
   * *Anti-Proxy Protection:* Rejects printed photos, screen replays, and unauthorized individuals.

---

## ⏱️ Task & Work Time Tracking System

* **Attendance-Gated Timers:** Employees can only initiate task timers after a verified physical clock-in.
* **Granular Time Hierarchy:** `Tenant` $\rightarrow$ `Project` $\rightarrow$ `Task` $\rightarrow$ `Work Log`.
* **Live Stopwatch & Manual Logging:** Real-time tracking with automatic pause triggers on break or office exit.
* **Discrepancy Analysis:** Automated comparison between **Shift Duration** (Office Presence) and **Productive Time** (Task Logs).

---

## 🚗 Verifiable Field-Visit & Route Tracking (Proof of Physical Visit - PoPV)

For employees visiting external clients, hospitals, dealers, or distributors:
* **Destination Geofencing (PostGIS):** Client locations configured with tight geofence radiuses (50m–100m).
* **Enforced Dwell Time (Anti-Drive-By):** Employees must physically remain at the destination for a minimum required duration (**default: 30 minutes**, configurable by employer per tenant or per destination) before the visit can be marked as completed.
* **Tamper-Proof Live Photo Proof:** Direct camera capture with cryptographic watermarking (time, GPS, client name, server hash). Gallery uploads are strictly forbidden.
* **Client SMS / WhatsApp OTP Counter-Verification:** A 4-digit OTP is sent to the client's (doctor, dealer, distributor) registered phone via SMS or WhatsApp. The employee must enter the OTP to finalize the visit, proving they actually met the contact person.
* **Planned vs. Actual Itinerary Audit:** Continuous background breadcrumbs to detect unauthorized detours, track vehicle travel distance (mileage audit), and compare planned beats against actual visits.
* **Transport Mode & Vehicle Mileage Tracking:** Employees declare transport mode (Company Car, Personal Car, Two-Wheeler, Cab, Public Transport) and select assigned vehicle at shift start. GPS breadcrumb polyline computes exact per-leg kilometers via PostGIS `ST_Length`. Odometer start/end photos provide anti-fraud cross-verification against GPS distance. Automatic transport-mode-based reimbursement calculation with employer-configurable per-km rates.

---

## 🗄️ Multi-Tenancy Architecture

* **Database Strategy:** Shared Database with PostgreSQL **Row-Level Security (RLS)**.
* Every tenant data table contains a `tenant_id` column.
* Database policies enforce that connections can only view and modify records matching `current_setting('app.current_tenant_id')`.
* **Zero Cross-Tenant Leakage Risk:** Enforced at the SQL engine level.

---

## 📁 Repository Structure (Monorepo Blueprint)

```
zuigo-attendance-system/
├── backend/                  # Python FastAPI Backend
│   ├── app/
│   │   ├── api/              # API Endpoints (v1)
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── attendance.py
│   │   │   │   ├── kiosk.py
│   │   │   │   ├── tasks.py
│   │   │   │   ├── employees.py
│   │   │   │   └── reports.py
│   │   ├── core/             # Config, security, database session, Redis
│   │   ├── models/           # SQLAlchemy / SQLModel models (with RLS)
│   │   ├── schemas/          # Pydantic schemas (request/response)
│   │   ├── services/         # Business logic (QR generator, facial match, verification)
│   │   └── main.py           # FastAPI entrypoint
│   ├── alembic/              # Database migrations
│   ├── tests/                # Unit & integration test suites
│   ├── Dockerfile
│   └── pyproject.toml
│
├── apps/
│   ├── kiosk-web/            # Lightweight Laptop Web App (Vite + React + Tailwind)
│   │   ├── src/
│   │   │   ├── components/   # Rotating QR canvas, clock, status indicator
│   │   │   ├── hooks/        # WebSocket / SSE connection to backend
│   │   │   └── App.tsx
│   │   └── package.json
│   │
│   ├── mobile/               # Employee Mobile App (React Native / Expo)
│   │   ├── src/
│   │   │   ├── screens/      # Check-in, Liveness Camera, Task Stopwatch, Profile
│   │   │   ├── services/     # Keystore/Secure Enclave, Camera ML, Network info
│   │   │   └── navigation/
│   │   └── package.json
│   │
│   └── admin-web/            # Employer Management & Live Presence Dashboard
│       └── ...
│
├── docker/
│   ├── docker-compose.yml    # Postgres (PostGIS), Redis, Backend, Kiosk
│   └── postgres-init/        # Init scripts with PostGIS extension & RLS
│
├── docs/                     # Specifications, DB Schemas, API Contracts
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   └── API_SPECIFICATION.md
│
├── .gitignore
└── README.md
```

---

---

## 🚀 Getting Started & How to Run

Follow these step-by-step instructions to run the entire ZuiGO Attendance System locally.

### 📋 Prerequisites

Ensure you have the following installed on your machine:
* **Python 3.12+**
* **Node.js 18+ & npm**
* **Docker & Docker Compose** (for PostgreSQL PostGIS and Redis)

---

### Step 1: Clone Repository & Virtual Environment Setup

```bash
# Clone the repository
git clone https://github.com/ZuiGO/ZuiGO-Attendance-System.git
cd ZuiGO-Attendance-System

# Create and activate Python virtual environment
cd backend
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
cd ..
```

---

### Step 2: Start Infrastructure (PostgreSQL PostGIS + Redis)

Use Docker Compose to launch PostgreSQL 16 with PostGIS 3.4 and Redis 7 in detached mode:

```bash
cd docker
docker compose up -d
cd ..
```

This starts:
* **PostgreSQL with PostGIS**: `localhost:5432` (Database: `zuigo_attendance`, User: `zuigo`)
* **Redis**: `localhost:6379` (Nonce cache & Dynamic QR TTL tracking)

---

### Step 3: Initialize Database Schema & Seed Demo Data

Run the automated initializer to enable PostGIS extensions, create all 18 tables, and populate realistic enterprise demo data:

```powershell
# 1. Initialize schema and extensions (uuid-ossp, pgcrypto, postgis)
python backend/scripts/init_db.py

# 2. Seed multi-tenant demo records (Tenant, Offices, Employees, Hospitals, Vehicles)
python backend/scripts/seed_data.py
```

#### 🔑 Demo Accounts Seeded:
| Name | Email | Role | Department | Default Password |
|:---|:---|:---:|:---|:---:|
| **Jayesh Admin** | `jayesh@zuigo.ai` | `ADMIN` | Engineering | `password123` |
| **Alex Johnson** | `alex.j@zuigo.ai` | `EMPLOYEE` | Field Operations | `password123` |
| **Priya Sharma** | `priya.s@zuigo.ai` | `EMPLOYEE` | Hospital Relations | `password123` |
| **Rahul Verma** | `rahul.v@zuigo.ai` | `MANAGER` | Field Operations | `password123` |

* **Demo Tenant Subdomain:** `zuigo` (Header: `X-Tenant-ID: <tenant-uuid>` or subdomain routing)
* **Demo Kiosk API Key:** `kiosk_hq_dev_key_2026`

---

### Step 4: Run Automated Test Suite (54/54 Tests Passing)

Execute the full automated test suite covering zero-trust QR nonces, face similarity thresholding, 30-minute dwell time gates, travel fraud alerts, office geofence locations, and admin dashboards:

```powershell
# Windows
.\backend\.venv\Scripts\pytest.exe -v backend/tests

# Linux / macOS
pytest -v backend/tests
```

---

### Step 5: Start the FastAPI Backend Service

```powershell
# Windows
.\backend\.venv\Scripts\uvicorn.exe app.main:app --app-dir backend --reload --port 8000

# Linux / macOS
uvicorn app.main:app --app-dir backend --reload --port 8000
```

* **Interactive Swagger UI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Health Check Probe:** [http://localhost:8000/health](http://localhost:8000/health)

---

### Step 6: Start Laptop Dynamic QR Kiosk Web App

The lightweight kiosk web application runs on any laptop screen placed at the office entrance, generating a single-use HMAC-SHA256 rotating QR code every 15 seconds:

```bash
cd apps/kiosk-web
npm install
npm run dev
```

* **Kiosk Terminal URL:** [http://localhost:5173](http://localhost:5173)

---

### Step 7: Start Employer Management & Live Presence Dashboard

The web management portal gives administrators real-time presence visibility, field visit beat monitoring, and travel reimbursement approval controls:

```bash
cd apps/admin-web
npm install
npm run dev
```

* **Employer Dashboard URL:** [http://localhost:5174](http://localhost:5174)

---

### Step 8: Start Employee React Native Mobile App

The cross-platform React Native / Expo application allows employees to scan rotating QR codes, verify 1-sec selfie liveness, manage task stopwatches, execute 30-min field visits, and capture odometer shifts:

```bash
cd apps/mobile
npm install
npm start
```

* Press `a` in terminal to launch in **Android Emulator**.
* Press `i` to launch in **iOS Simulator**.
* Scan QR code with the **Expo Go** app on a physical Android or iOS device.

---

## 🧪 Key Endpoints & Architectural Highlights

| Method | Endpoint | Description | Anti-Fraud Defense |
|:---:|:---|:---|:---|
| `GET` | `/api/v1/kiosk/qr-stream` | Dynamic QR code WebSocket & polling stream | Signed HMAC-SHA256, 15-sec TTL, single-use Redis nonce |
| `POST` | `/api/v1/attendance/clock-in` | Zero-trust physical presence check-in | 1:1 hardware device bind, mock GPS check, BSSID geofence, 1-sec face liveness |
| `POST` | `/api/v1/tasks/timer/start` | Attendance-gated task stopwatch start | Rejects unclocked employees; auto-pauses overlapping timers |
| `POST` | `/api/v1/field/stop/arrive` | Destination arrival check-in | 75m PostGIS geofence; triggers mandatory 30-min dwell timer |
| `POST` | `/api/v1/field/visit/complete` | Proof of Physical Visit (PoPV) completion | 30-min dwell enforcement + client SMS/WhatsApp 4-digit OTP |
| `POST` | `/api/v1/travel/shift/end` | Mileage log submission | Compares odometer vs GPS polyline; flags $> 15\%$ fraud discrepancy |
| `GET` | `/api/v1/admin/presence/live` | Employer live presence & task ticker board | Real-time presence %, active dwell counters, live task stopwatches |
| `POST` | `/api/v1/admin/policies` | Policy configuration studio | Configurable 15m–120m dwell time, OTP channels, and ₹/km travel rates |
