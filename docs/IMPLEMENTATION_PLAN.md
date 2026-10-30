# ZuiGO Attendance System — Detailed Implementation Plan & Roadmap

This document outlines the step-by-step phased execution plan. Development will only commence upon explicit user confirmation.

---

## 📅 Phase 1: Foundation, Infrastructure & Database Setup
* **Milestone 1.1: Docker Compose Environment**
  * PostgreSQL 16 image with PostGIS extension.
  * Redis 7 image with persistence enabled.
  * Local networking and environment variable bindings.
* **Milestone 1.2: FastAPI Backend Scaffolding**
  * Poetry / Pipenv dependency configuration (`fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `geoalchemy2`, `alembic`, `redis-py`, `pydantic`, `pyjwt`, `cryptography`).
  * Asynchronous database engine setup with session factory.
  * Multi-tenant middleware extracting `tenant_id` from subdomain/header and setting PostgreSQL `app.current_tenant_id`.
* **Milestone 1.3: Alembic Database Migrations**
  * Create migrations for: `tenants`, `offices`, `departments`, `employees`, `attendance_records`, `projects`, `tasks`, `task_time_entries`.
  * Enable PostGIS extension and Row-Level Security (RLS) policies.
  * Seed initial test tenant (`ZuiGO`), test office with geofence and authorized Wi-Fi BSSID, and sample employees.

---

## 📅 Phase 2: Laptop Kiosk Web Application & Dynamic Token Engine
* **Milestone 2.1: Dynamic QR Rotation Service (Backend)**
  * Cryptographic HMAC-SHA256 token generator.
  * Redis token cache with 20-second TTL and atomic `GETDEL` validation.
  * FastAPI WebSocket endpoint for live token streaming.
* **Milestone 2.2: Lightweight Laptop Web Kiosk (Vite + React)**
  * Fullscreen responsive UI showing:
    * Office Name & Real-time Clock.
    * High-contrast dynamic QR code regenerating smoothly every 15 seconds.
    * Animated countdown progress bar.
    * Connection status indicator (Active / Reconnecting).

---

## 📅 Phase 3: React Native Mobile Client & MFPV Attendance Pipeline
* **Milestone 3.1: Mobile Foundation & Device Binding**
  * React Native / Expo application scaffolding.
  * Hardware Keystore / Secure Enclave integration for asymmetric key pair generation.
  * Device registration and baseline photo/facial embedding onboarding flow.
* **Milestone 3.2: Multi-Factor Presence Verification (MFPV) Engine**
  * QR Code camera scanner.
  * Wi-Fi BSSID and SSID collector (`react-native-network-info`).
  * Location service with mock-location / fake GPS detection.
  * On-device facial liveness check and embedding matcher.
  * Single payload submission to `/api/v1/attendance/clock-in`.
* **Milestone 3.3: Attendance Management Screens**
  * Daily attendance status card (Clocked In, Shift Duration, Clock Out button).
  * Monthly attendance calendar and history view.

---

## 📅 Phase 4: Task & Work Time Tracking System
* **Milestone 4.1: Task API & State Machine (Backend)**
  * CRUD endpoints for Projects and Tasks.
  * Timer endpoints (`start`, `stop`, `pause`) strictly gated by active daily attendance.
  * Automatic stop triggers on clock-out or geofence exit.
* **Milestone 4.2: Mobile Task Tracker UI**
  * "My Tasks" board with filters (Today, In Progress, Completed).
  * Floating persistent timer widget with Start / Pause / Stop controls.
  * Daily timesheet review and manual work log entry dialog.

---

## 📅 Phase 5: Employer Dashboard & Compliance Analytics
* **Milestone 5.1: Real-Time Presence Board**
  * Live list of present employees, arrival times, and currently active tasks.
  * Live office attendance percentage.
* **Milestone 5.2: Productive Time vs. Attendance Analytics**
  * Visual discrepancy charts: Gross shift time vs. tracked task time.
  * Exportable payroll-ready reports (CSV/Excel/PDF).
  * Late arrival, half-day, and overtime rule evaluation.

---

## 🧪 Quality Assurance & Anti-Proxy Test Suite

| Test Case | Scenario | Expected Outcome |
| :--- | :--- | :--- |
| **TC-01** | Employee takes photo of dynamic QR on laptop and sends to friend remotely. | Friend's scan rejected: `QR_EXPIRED_OR_REUSED` (token expired > 15s). |
| **TC-02** | Remote scan attempted within 15 seconds using fake GPS app. | Rejected: `NETWORK_MISMATCH` (office Wi-Fi BSSID missing). |
| **TC-03** | Coworker logs into friend's account on their phone. | Rejected: `DEVICE_MISMATCH` (hardware key signature mismatch). |
| **TC-04** | Employee scans QR but points camera at printed photo of their face. | Rejected: `LIVENESS_FAILED` (no micro-facial movement / 3D depth). |
| **TC-05** | Employee attempts to start a task timer while not clocked in. | Rejected: `403 Forbidden` (`ATTENDANCE_REQUIRED`). |
| **TC-06** | Tenant A attempts to query Tenant B's employee list or timesheets. | PostgreSQL RLS returns empty set (Zero data leakage). |
