# ZuiGO Attendance System — API Specification (FastAPI)

Base Path: `/api/v1`

---

## 1. Authentication & Device Onboarding

### 1.1 Employee Login & Device Enrollment
* **Endpoint:** `POST /api/v1/auth/enroll-device`
* **Description:** Binds the employee's physical smartphone to their account upon initial onboarding.
* **Request Body:**
  ```json
  {
    "email": "alex@acme.com",
    "password": "TemporaryPassword123!",
    "device_id": "hw-d92fa84b-91c1-4b72",
    "device_public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w...",
    "device_model": "iPhone 15 Pro",
    "os_version": "iOS 17.5"
  }
  ```
* **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "employee": {
      "id": "e4b3e839-4cb5-4f3e-8e68-07df9706dbb7",
      "full_name": "Alex Johnson",
      "role": "EMPLOYEE",
      "requires_baseline_face": true
    }
  }
  ```

### 1.2 Baseline Face Enrollment
* **Endpoint:** `POST /api/v1/auth/enroll-face`
* **Description:** Submits the initial verified facial embedding vector taken during HR onboarding.
* **Request Body:**
  ```json
  {
    "face_embedding": [0.0432, -0.1983, 0.0872, ..., 0.1245] // 128 or 512 dimensions
  }
  ```
* **Response (200 OK):**
  ```json
  {
    "status": "ENROLLED",
    "message": "Facial baseline registered successfully"
  }
  ```

---

## 2. Kiosk Display (Laptop Screen Dynamic QR Engine)

### 2.1 Dynamic QR WebSocket Feed
* **Endpoint:** `GET /api/v1/kiosk/qr-stream` (WebSocket)
* **Headers:** `X-Kiosk-Key: <kiosk_api_key>`
* **Server Push (Every 15 Seconds):**
  ```json
  {
    "type": "QR_REFRESH",
    "data": {
      "tenant_id": "c7e8e58a-3642-4f30-8025-4b0717fb0534",
      "office_id": "d1e7c53a-4421-4f11-8933-4b0717fb0112",
      "timestamp": 1730291400,
      "nonce": "8f8b89e2-9b51-4091-a1b4-7d52a781b0a3",
      "signature": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "expires_in_seconds": 15
    }
  }
  ```

---

## 3. Physical Attendance Verification (Zero-Trust Pipeline)

### 3.1 Verify & Clock In
* **Endpoint:** `POST /api/v1/attendance/clock-in`
* **Security:** Bearer Token (Bound Employee Device)
* **Request Body:**
  ```json
  {
    "qr_payload": {
      "tenant_id": "c7e8e58a-3642-4f30-8025-4b0717fb0534",
      "office_id": "d1e7c53a-4421-4f11-8933-4b0717fb0112",
      "timestamp": 1730291400,
      "nonce": "8f8b89e2-9b51-4091-a1b4-7d52a781b0a3",
      "signature": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    "network_audit": {
      "wifi_bssid": "3c:37:12:89:af:90",
      "wifi_ssid": "ZuiGO-Office-5G"
    },
    "location": {
      "latitude": 28.535517,
      "longitude": 77.391029,
      "is_mock": false
    },
    "face_verification": {
      "liveness_passed": true,
      "captured_embedding": [0.0430, -0.1980, 0.0871, ..., 0.1240]
    },
    "device_signature": "MEQCIAz7xL+..."
  }
  ```
* **Response (200 OK):**
  ```json
  {
    "attendance_id": "7bf3b934-8c81-4221-a477-8316c0228bb4",
    "status": "PRESENT",
    "clock_in_time": "2026-10-30T09:02:15Z",
    "similarity_score": 0.9852,
    "message": "Physical presence confirmed. Clocked in successfully."
  }
  ```
* **Error Responses:**
  * `400 Bad Request` — `QR_EXPIRED_OR_REUSED`: QR nonce has already been consumed or timed out.
  * `403 Forbidden` — `NETWORK_MISMATCH`: Wi-Fi BSSID does not match registered office access points.
  * `403 Forbidden` — `DEVICE_MISMATCH`: Request submitted from an unauthorized hardware device.
  * `422 Unprocessable Entity` — `LIVENESS_FAILED`: Facial scan failed anti-spoofing check.

### 3.2 Clock Out
* **Endpoint:** `POST /api/v1/attendance/clock-out`
* **Request Body:**
  ```json
  {
    "attendance_id": "7bf3b934-8c81-4221-a477-8316c0228bb4",
    "location": {
      "latitude": 28.535520,
      "longitude": 77.391035
    }
  }
  ```
* **Response (200 OK):**
  ```json
  {
    "attendance_id": "7bf3b934-8c81-4221-a477-8316c0228bb4",
    "clock_out_time": "2026-10-30T18:15:30Z",
    "total_shift_hours": 9.22,
    "active_tasks_stopped": 1
  }
  ```

---

## 4. Task & Work Time Tracking

### 4.1 List Assigned Tasks
* **Endpoint:** `GET /api/v1/tasks/my-tasks?status=IN_PROGRESS,TODO`
* **Response (200 OK):**
  ```json
  [
    {
      "id": "9a12c842-1209-4821-b183-93821038aa82",
      "project_name": "Mobile App V2",
      "title": "Implement On-Device Liveness Verification",
      "status": "IN_PROGRESS",
      "priority": "HIGH",
      "tracked_seconds_today": 7200
    }
  ]
  ```

### 4.2 Start Task Timer (Attendance Gated)
* **Endpoint:** `POST /api/v1/tasks/{task_id}/timer/start`
* **Pre-condition:** Employee must have an active `attendance_record` with `clock_out IS NULL`.
* **Response (200 OK):**
  ```json
  {
    "time_entry_id": "31b2c418-8092-411a-82bc-90184b238e89",
    "task_id": "9a12c842-1209-4821-b183-93821038aa82",
    "start_time": "2026-10-30T09:15:00Z",
    "status": "RUNNING"
  }
  ```

### 4.3 Stop / Pause Task Timer
* **Endpoint:** `POST /api/v1/tasks/{task_id}/timer/stop`
* **Request Body:**
  ```json
  {
    "time_entry_id": "31b2c418-8092-411a-82bc-90184b238e89",
    "notes": "Completed initial camera stream capture hook"
  }
  ```
* **Response (200 OK):**
  ```json
  {
    "time_entry_id": "31b2c418-8092-411a-82bc-90184b238e89",
    "duration_seconds": 5400,
    "formatted_duration": "1h 30m"
  }
  ```

---

## 5. Employer / Manager Live Dashboard

### 5.1 Real-Time Office Presence Board
* **Endpoint:** `GET /api/v1/admin/presence/live`
* **Response (200 OK):**
  ```json
  {
    "total_present": 42,
    "total_expected": 50,
    "presence_rate_percentage": 84.0,
    "employees": [
      {
        "id": "e4b3e839-4cb5-4f3e-8e68-07df9706dbb7",
        "name": "Alex Johnson",
        "clock_in_time": "09:02 AM",
        "current_active_task": "Implement On-Device Liveness Verification",
        "active_task_elapsed_seconds": 3200,
        "status": "WORKING"
      }
    ]
  }
  ```
