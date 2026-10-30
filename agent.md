# ZuiGO Attendance System — Agent Continuity Document

> **Purpose:** This document tracks the current build state, completed work, test results, in-progress items, and next steps so any agent can resume seamlessly without lost context.

---

## 🔄 Current State

| Field | Value |
|:---|:---|
| **Current Phase** | Phase 1 to Phase 5: Core Services & React Native Mobile App Built & Tested |
| **Status** | 🟢 ALL TESTS PASSING (35/35 Passed in 5.94s) |
| **Last Updated** | 2026-10-30T14:38:30+05:30 |
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
- [x] Registered all 18 SQLAlchemy 2.0 ORM models in `backend/app/models/`.

### 2. Dynamic Rotating QR Engine & Laptop Kiosk (Phase 2)
- [x] Pydantic schemas (`backend/app/schemas/kiosk.py`).
- [x] Dynamic QR cryptographic HMAC-SHA256 generation with 15s validity and Redis single-use nonce caching (`backend/app/services/qr_service.py`).
- [x] Single-use atomic consumption (`GETDEL` / pop): duplicate/reused QR tokens are immediately rejected.
- [x] Kiosk API endpoints (`backend/app/api/v1/kiosk.py`) supporting HTTP polling and WebSocket streaming (`/qr-stream`).
- [x] Lightweight Laptop Web Kiosk frontend (`apps/kiosk-web/`).

### 3. React Native Employee Mobile App (Phase 3)
- [x] Cross-platform React Native / Expo application (`apps/mobile/`):
  - Hardware device binding (`src/services/deviceSecurity.ts`): binds physical smartphone UUID & keypair.
  - Network presence & mock GPS detector (`src/services/networkDetector.ts`): extracts Wi-Fi BSSID and flags OS mock locations.
  - 1-second on-device selfie facial liveness scan (`src/services/livenessDetector.ts`).
  - Secure authentication & attendance context providers (`src/context/`).
  - Interactive screens:
    - `LoginScreen.tsx`: Company login with hardware device binding badge.
    - `DashboardScreen.tsx`: Attendance hero card, active task timer banner, quick action grid.
    - `OfficeScanScreen.tsx`: Dynamic QR viewfinder + 1-sec selfie liveness prompt + clock-in.
    - `TaskStopwatchScreen.tsx`: Attendance-gated task stopwatch (locked when not clocked in).
    - `FieldVisitScreen.tsx`: 50+ client stops, 75m geofence arrival, **30-min dwell countdown bar**, client SMS/WhatsApp OTP modal.
    - `TravelShiftScreen.tsx`: Transport mode selector (Car/Bike/Cab), start/end odometer photo capture, and 15% fraud discrepancy alert.

### 4. Task & Work Time Tracking Subsystem (Phase 4)
- [x] Attendance-gated task stopwatch engine (`backend/app/services/task_service.py`).
- [x] Single active timer rule & auto-stop on clock-out.
- [x] Task API endpoints (`backend/app/api/v1/tasks.py`).

### 5. Verifiable Field-Visit, Transport & Mileage Tracking (Phase 5)
- [x] Field Visit Service (`backend/app/services/field_visit_service.py`) with 30-min minimum dwell time and client SMS/WhatsApp OTP counter-verification.
- [x] Travel & Mileage Service (`backend/app/services/travel_service.py`) with odometer fraud detection (>15% discrepancy alert) and automated reimbursement.

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
