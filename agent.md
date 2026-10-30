# ZuiGO Attendance System — Agent Continuity Document

> **Purpose:** This document tracks the current build state, completed work, test results, in-progress items, and next steps so any agent can resume seamlessly without lost context.

---

## 🔄 Current State

| Field | Value |
|:---|:---|
| **Current Phase** | Phase 1 to Phase 5: Core Services Built & Tested |
| **Status** | 🟢 ALL TESTS PASSING (35/35 Passed in 9.24s) |
| **Last Updated** | 2026-10-30T14:29:30+05:30 |
| **Branch** | `main` |
| **Repo** | https://github.com/ZuiGO/ZuiGO-Attendance-System |

---

## ✅ Completed Modules & Verified Features

### 1. Foundation & Infrastructure (Phase 1)
- [x] Docker Compose environment (`docker/docker-compose.yml`) with PostgreSQL 16 + PostGIS 3.4 and Redis 7.
- [x] PostGIS extension and RLS initialization SQL (`docker/postgres-init/01_extensions.sql`).
- [x] Pydantic Settings configuration (`backend/app/core/config.py`) with 30-min dwell time, 15-sec QR TTL, reimbursement rates.
- [x] Async SQLAlchemy 2.0 Engine & Sessionmaker (`backend/app/core/database.py`).
- [x] Redis connection pool manager (`backend/app/core/redis.py`).
- [x] Multi-Tenant middleware (`backend/app/core/tenant.py`) supporting `X-Tenant-ID` header and subdomain routing.
- [x] Native bcrypt password hashing and JWT access token creation/decoding (`backend/app/core/security.py`).
- [x] Registered all 18 SQLAlchemy 2.0 ORM models in `backend/app/models/`:
  - `tenants`, `offices`, `departments`, `employees`
  - `attendance_records`
  - `projects`, `tasks`, `task_time_entries`
  - `client_destinations`, `field_itineraries`, `field_visit_stops`, `field_visit_proofs`, `client_otp_verifications`
  - `vehicles`, `travel_logs`, `travel_legs`, `travel_expense_receipts`
  - `location_breadcrumbs`

### 2. Dynamic Rotating QR Engine & Laptop Kiosk (Phase 2)
- [x] Pydantic schemas (`backend/app/schemas/kiosk.py`).
- [x] Dynamic QR cryptographic HMAC-SHA256 generation with 15s validity and Redis single-use nonce caching (`backend/app/services/qr_service.py`).
- [x] Single-use atomic consumption (`GETDEL` / pop): duplicate/reused QR tokens are immediately rejected.
- [x] Kiosk API endpoints (`backend/app/api/v1/kiosk.py`) supporting HTTP polling and WebSocket streaming (`/qr-stream`).
- [x] Lightweight Laptop Web Kiosk frontend (`apps/kiosk-web/`):
  - Vite + React + TypeScript fullscreen terminal
  - Animated high-contrast rotating QR code canvas
  - 15-second dynamic countdown progress bar
  - Live clock and connection status pill with offline buffer fallback.

### 3. Multi-Factor Physical Presence Attendance (Phase 3)
- [x] Attendance schemas (`backend/app/schemas/attendance.py`) and auth schemas (`backend/app/schemas/auth.py`).
- [x] Attendance Verification Service (`backend/app/services/attendance_service.py`) executing 5 Zero-Trust verification pillars:
  1. Dynamic QR single-use nonce consumption.
  2. 1:1 Hardware device binding (`device_id`).
  3. OS-level mock location detection (`is_mock`).
  4. Office Wi-Fi BSSID network geofencing.
  5. On-device facial liveness check and cosine similarity matching ($>= 0.82$).
- [x] Attendance endpoints (`backend/app/api/v1/attendance.py`): `/clock-in` and `/clock-out`.

### 4. Task & Work Time Tracking Subsystem (Phase 4)
- [x] Task schemas (`backend/app/schemas/task.py`).
- [x] Task Tracking Service (`backend/app/services/task_service.py`):
  - **Attendance-Gated Timers:** Employees cannot start a task timer unless physically clocked in today.
  - **Single Active Timer Rule:** Starting a new task timer automatically stops/pauses any prior active timer.
  - **Auto-Stop on Clock-Out:** Clocking out automatically closes open task timers.
- [x] Task API endpoints (`backend/app/api/v1/tasks.py`).

### 5. Verifiable Field-Visit, Transport & Mileage Tracking (Phase 5)
- [x] Field visit schemas (`backend/app/schemas/field_visit.py`) and travel schemas (`backend/app/schemas/travel.py`).
- [x] Field Visit Service (`backend/app/services/field_visit_service.py`):
  - Client destination geofencing ($< 75\text{m}$).
  - **30-Minute Dwell-Time Enforcement (Anti-Drive-By):** Blocks completion if duration at client is $< 30$ mins.
  - **Client SMS / WhatsApp OTP Verification:** Dispatches 4-digit OTP to client contact with 5-min TTL and 3-attempt limit.
  - Tamper-proof in-app camera photo proof with cryptographic watermark.
- [x] Field API endpoints (`backend/app/api/v1/field.py`).
- [x] Travel & Mileage Service (`backend/app/services/travel_service.py`):
  - Fleet and personal vehicle registry (`/travel/vehicles`).
  - Odometer start & end photo capture.
  - **Anti-Fraud Odometer Discrepancy Alert:** Flags any shift where odometer distance exceeds GPS distance by $> 15\%$.
  - Automated reimbursement computation based on transport mode (Personal Car ₹8/km, Two-Wheeler ₹4/km).
- [x] Travel API endpoints (`backend/app/api/v1/travel.py`).

---

## 🧪 Automated Test Suite (35/35 PASSED)

Run with: `backend\.venv\Scripts\pytest.exe -v backend/tests`

| Test Module | Coverage Area | Tests | Status |
|:---|:---|:---:|:---:|
| `test_config.py` | Settings defaults (30m dwell, 15s QR, rates) | 1 | 🟢 PASS |
| `test_health_api.py` | Health, readiness, CORS headers | 3 | 🟢 PASS |
| `test_models.py` | All 18 SQLAlchemy 2.0 tables and columns | 5 | 🟢 PASS |
| `test_security.py` | Bcrypt, JWT tokens, QR HMAC, expiration, replay | 6 | 🟢 PASS |
| `test_tenant_middleware.py` | Subdomain & X-Tenant-ID header resolution | 3 | 🟢 PASS |
| `test_kiosk_service.py` | QR generation & atomic single-use nonce consumption | 3 | 🟢 PASS |
| `test_attendance_service.py` | Cosine similarity & Haversine geofence calculations | 6 | 🟢 PASS |
| `test_task_service.py` | Format seconds & attendance gating logic | 1 | 🟢 PASS |
| `test_field_visit_service.py` | Phone masking, 75m geofence, 30-min dwell time logic | 3 | 🟢 PASS |
| `test_travel_service.py` | Mileage formulas, odometer discrepancy fraud alert | 4 | 🟢 PASS |
| **Total** | | **35** | 🟢 **100% PASS** |

---

## 🗂️ File Map

```
backend/
├── app/
│   ├── main.py                     # FastAPI application entrypoint
│   ├── core/
│   │   ├── config.py               # Pydantic Settings
│   │   ├── database.py             # Async SQLAlchemy Engine & Session
│   │   ├── redis.py                # Async Redis Client
│   │   ├── security.py             # Bcrypt, JWT, HMAC QR generator
│   │   ├── tenant.py               # Multi-Tenant Middleware
│   │   └── dependencies.py         # Auth & Tenant dependency injection
│   ├── models/                     # 18 SQLAlchemy 2.0 Models
│   │   ├── tenant.py, employee.py, attendance.py, task.py
│   │   └── field_visit.py, travel.py, location.py
│   ├── schemas/                    # Pydantic v2 validation schemas
│   │   ├── auth.py, kiosk.py, attendance.py, task.py
│   │   └── field_visit.py, travel.py
│   ├── services/                   # Business Logic Layer
│   │   ├── qr_service.py           # Rotating QR & Redis single-use nonces
│   │   ├── attendance_service.py   # MFPV presence verification engine
│   │   ├── task_service.py         # Attendance-gated task stopwatch
│   │   ├── field_visit_service.py  # 30-min dwell time & client OTP
│   │   └── travel_service.py       # Mileage & 15% discrepancy fraud alert
│   └── api/v1/                     # FastAPI Route Controllers
│       ├── kiosk.py, attendance.py, tasks.py, field.py, travel.py
│       └── __init__.py             # Aggregated API router
├── tests/                          # 35 Automated Pytest unit & integration tests
├── Dockerfile
└── requirements.txt
apps/
└── kiosk-web/                      # Laptop Screen Dynamic QR Terminal (Vite + React)
    ├── src/
    │   ├── App.tsx                 # Fullscreen terminal UI
    │   ├── hooks/useDynamicQR.ts   # 15s countdown & WebSocket hook
    │   └── main.tsx
    ├── package.json
    └── vite.config.ts
docker/
├── docker-compose.yml              # PostGIS 16 + Redis 7 + Backend
└── postgres-init/01_extensions.sql
```

---

## 📋 Next Recommended Steps
1. **React Native Mobile App:** Scaffold `apps/mobile/` with camera liveness, QR scanner, Wi-Fi BSSID fetcher, and field visit check-in screens.
2. **Employer Web Dashboard:** Build the management interface for live presence boards, beat planning, and mileage reimbursement approvals.
