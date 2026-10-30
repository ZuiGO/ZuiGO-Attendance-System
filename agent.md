# ZuiGO Attendance System — Agent Continuity Document

> **Purpose:** This document tracks the current build state, completed work, in-progress items, and next steps so any agent can resume seamlessly.

---

## 🔄 Current State

| Field | Value |
|:---|:---|
| **Current Phase** | Phase 1: Foundation, Infrastructure & Database Setup (COMPLETED) → Moving to Phase 2 |
| **Status** | 🟢 PHASE 1 TESTS PASSING (18/18 Passed) |
| **Last Updated** | 2026-10-30T13:51:30+05:30 |
| **Last Commit** | Pending Git Commit for Phase 1 Core |
| **Branch** | `main` |
| **Repo** | https://github.com/ZuiGO/ZuiGO-Attendance-System |

---

## ✅ Completed

### Planning & Documentation (PRE-BUILD)
- [x] GitHub repo created and configured (`ZuiGO/ZuiGO-Attendance-System`)
- [x] README.md with full system overview
- [x] docs/ARCHITECTURE.md — Zero-trust MFPV protocol, field-visit PoPV, transport tracking
- [x] docs/DATABASE_SCHEMA.md — 18 tables with PostGIS, RLS, indexes
- [x] docs/API_SPECIFICATION.md — All endpoint contracts (auth, attendance, kiosk, tasks, field visits, travel)
- [x] docs/IMPLEMENTATION_PLAN.md — 6-phase roadmap with test cases

### Phase 1: Foundation, Infrastructure & Database Setup
- [x] Milestone 1.1: Docker Compose Environment
  - `docker/docker-compose.yml` (PostGIS 16 + Redis 7 + Backend container)
  - `docker/postgres-init/01_extensions.sql` (uuid-ossp, pgcrypto, postgis, RLS configs)
  - `.env.example` with all configuration parameters
  - `backend/pyproject.toml` and `backend/requirements.txt`
  - `backend/Dockerfile`
- [x] Milestone 1.2: FastAPI Backend Scaffolding
  - `backend/app/main.py` (FastAPI app, CORS, lifespan, exception handlers)
  - `backend/app/core/config.py` (Pydantic Settings with 30m dwell, 15s QR, reimbursement rates)
  - `backend/app/core/database.py` (Async SQLAlchemy engine, sessionmaker, tenant contextvar)
  - `backend/app/core/redis.py` (Async Redis client with connection pooling)
  - `backend/app/core/security.py` (Native bcrypt hashing, JWT access tokens, dynamic QR HMAC-SHA256 generator & verifier)
  - `backend/app/core/tenant.py` (Multi-tenant middleware supporting `X-Tenant-ID` header and subdomain routing)
  - `backend/app/core/dependencies.py` (FastAPI auth & tenant dependencies, role checkers)
- [x] Milestone 1.3: SQLAlchemy ORM Models (SQLAlchemy 2.0 `mapped_column` / `Mapped`)
  - `models/tenant.py` (`Tenant`, `Office`)
  - `models/employee.py` (`Department`, `Employee` with 1:1 hardware device binding & face embeddings)
  - `models/attendance.py` (`AttendanceRecord` with anti-proxy audit, PostGIS geometry, Wi-Fi BSSID)
  - `models/task.py` (`Project`, `Task`, `TaskTimeEntry`)
  - `models/field_visit.py` (`ClientDestination`, `FieldItinerary`, `FieldVisitStop`, `FieldVisitProof`, `ClientOtpVerification`)
  - `models/travel.py` (`Vehicle`, `TravelLog`, `TravelLeg`, `TravelExpenseReceipt`)
  - `models/location.py` (`LocationBreadcrumb`)
- [x] Milestone 1.4 & 1.5: Automated Testing Suite
  - `tests/test_config.py` (100% PASS)
  - `tests/test_security.py` (100% PASS)
  - `tests/test_tenant_middleware.py` (100% PASS)
  - `tests/test_models.py` (100% PASS — all 18 tables verified)
  - `tests/test_health_api.py` (100% PASS)
  - **Test Results:** 18/18 tests passed in 5.19s.

---

## 🏗️ Phase 2: Laptop Kiosk & Dynamic Rotating QR Engine (NEXT)

### Milestone 2.1: Dynamic QR Rotation Service (Backend)
- [ ] Pydantic Schemas for Kiosk QR generation (`schemas/kiosk.py`)
- [ ] Dynamic QR service (`services/qr_service.py`) integrating Redis single-use nonce storage (`SETEX` 20s, `GETDEL`)
- [ ] WebSocket / SSE endpoint for streaming QR tokens to Laptop screen (`api/v1/kiosk.py`)
- [ ] Automated tests for QR WebSocket and Redis nonce invalidation

### Milestone 2.2: Lightweight Laptop Web Kiosk (Vite + React)
- [ ] Scaffold `apps/kiosk-web/` with Vite, React, TypeScript, TailwindCSS
- [ ] Fullscreen Kiosk UI with animated 15s rotating dynamic QR code
- [ ] Live countdown progress bar and auto-reconnect WebSocket hook
- [ ] Office name & real-time clock header

---

## 📋 Upcoming Phases

- **Phase 3:** React Native Mobile Client (MFPV, Hardware Binding, On-Device Face Liveness, QR Scanner)
- **Phase 4:** Task & Work Time Tracking Engine (Attendance-Gated Timers)
- **Phase 5:** Field-Visit, Transport & Mileage Tracking (PoPV, 30-min Dwell Time, SMS/WhatsApp OTP, Odometer Cross-Check)
- **Phase 6:** Employer Dashboard & Compliance Analytics

---

## 🧰 Tech Stack Reference

| Component | Technology | Version |
|:---|:---|:---|
| Backend | Python FastAPI | 3.11+ |
| Database | PostgreSQL + PostGIS | 16+ |
| Cache | Redis | 7+ |
| ORM | SQLAlchemy (async) + GeoAlchemy2 | 2.0+ |
| Migrations | Alembic | latest |
| Mobile | React Native / Expo | — |
| Kiosk | Vite + React + TypeScript | — |

---

## 🗂️ Key File Locations

```
backend/
  app/
    main.py              — FastAPI app entry
    core/                — Config, DB, Redis, Security, Tenant middleware
    models/              — SQLAlchemy ORM models
    schemas/             — Pydantic request/response schemas
    api/v1/              — API route handlers
    services/            — Business logic layer
  alembic/               — Database migrations
  tests/                 — Test suites
docker/
  docker-compose.yml     — Infrastructure orchestration
  postgres-init/         — DB init scripts
```

---

## ⚠️ Known Issues / Blockers
- None at this time.

---

## 📝 Notes for Next Agent
- Read docs/DATABASE_SCHEMA.md for the complete DDL — all 18 tables are specified there.
- Read docs/API_SPECIFICATION.md for endpoint contracts.
- Tenant config JSONB includes: grace periods, dwell time (30 min default), OTP channel, reimbursement rates, discrepancy threshold.
- All tables use `tenant_id` with PostgreSQL Row-Level Security.
- The `git config` user is `zuigo` / `jayesh@zuigo.ai`. Credentials are in Windows Credential Manager.
