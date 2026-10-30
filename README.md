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

## 📋 Implementation Roadmap

* **Phase 1:** Multi-tenant Foundation & Database Setup (PostgreSQL RLS + PostGIS + FastAPI Core).
* **Phase 2:** Laptop Kiosk Display & Dynamic Rotating QR Engine (Redis + WebSockets).
* **Phase 3:** React Native Mobile Client (Device Binding + Wi-Fi BSSID + Camera Liveness + QR Scanner).
* **Phase 4:** Task Management & Live Time Tracking Engine.
* **Phase 5:** Employer Analytics, Attendance Compliance & Reporting Dashboard.
