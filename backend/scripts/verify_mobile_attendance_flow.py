"""Verify Mobile QR Clock-In and Clock-Out Flow with Selfie and Office Wi-Fi vs Personal Internet."""

import sys
import os
import json
import urllib.request

BASE_URL = "http://127.0.0.1:8000/api/v1"

def http_post(url, data, headers):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            return response.getcode(), json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def test_attendance_flow():
    print("Testing Mobile Clock-In -> Location Ping -> Clock-Out Flow...")

    # 1. Employee Login
    headers = {"Content-Type": "application/json"}
    status, login_res = http_post(f"{BASE_URL}/auth/login", {
        "email": "priya.s@zuigo.ai",
        "password": "password123",
        "tenant_id": "zuigo"
    }, headers)
    assert status == 200, f"Login failed: {login_res}"
    token = login_res["access_token"]
    tenant_id = login_res["tenant_id"]
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id
    }

    # 2. Get dynamic QR token from kiosk
    req = urllib.request.Request(f"{BASE_URL}/kiosk/current-qr?kiosk_key=kiosk_hq_dev_key_2026")
    with urllib.request.urlopen(req) as resp:
        kiosk_res = json.loads(resp.read().decode("utf-8"))
    qr_payload = kiosk_res["data"]
    print("  1. Acquired Fresh Dynamic QR Nonce from Kiosk Terminal")

    # 3. Clock In with Selfie, Dynamic QR, and PERSONAL CELLULAR Internet
    baseline_vector = [0.12, 0.45, -0.67, 0.89, -0.23, 0.34, -0.15, 0.78] * 16
    clock_in_payload = {
        "qr_payload": qr_payload,
        "network_audit": {
            "wifi_bssid": "00:00:00:00:00:00",
            "wifi_ssid": "Personal 5G Hotspot",
            "network_type": "PERSONAL_CELLULAR"
        },
        "location": {
            "latitude": 28.4985,
            "longitude": 77.0890,
            "accuracy_meters": 5.0,
            "is_mock": False
        },
        "face_verification": {
            "liveness_passed": True,
            "captured_embedding": baseline_vector
        },
        "device_id": "DEV-SAMSUNG-S23-ULTRA",
        "selfie_image_base64": "data:image/jpeg;base64,sample_selfie_verification_base64_data"
    }

    status, clock_in_res = http_post(f"{BASE_URL}/attendance/clock-in", clock_in_payload, auth_headers)
    assert status == 200, f"Clock in failed: {clock_in_res}"
    attendance_id = clock_in_res["attendance_id"]
    assert clock_in_res["network_type"] == "PERSONAL_CELLULAR", f"Expected PERSONAL_CELLULAR, got {clock_in_res['network_type']}"
    assert clock_in_res["is_office_wifi"] is False, f"Expected is_office_wifi False"
    print(f"  2. Clock-In via Personal Internet Verified! Attendance ID: {attendance_id}, Network: {clock_in_res['network_type']}, Is Office Wi-Fi: {clock_in_res['is_office_wifi']}")

    # 4. Stream Telemetry Location Ping with Personal Cellular
    ping_payload = {
        "latitude": 28.5355,
        "longitude": 77.2600,
        "accuracy_meters": 8.0,
        "is_mock": False,
        "network_type": "PERSONAL_CELLULAR",
        "wifi_bssid": None
    }
    status, ping_res = http_post(f"{BASE_URL}/attendance/ping-location", ping_payload, auth_headers)
    assert status == 200, f"Ping failed: {ping_res}"
    print("  3. Telemetry Location Ping with Personal Cellular recorded successfully")

    # 5. Check-Out with Selfie and Network Audit
    clock_out_payload = {
        "attendance_id": attendance_id,
        "location": {
            "latitude": 28.5355,
            "longitude": 77.2600,
            "accuracy_meters": 8.0,
            "is_mock": False
        },
        "network_audit": {
            "wifi_bssid": "00:00:00:00:00:00",
            "wifi_ssid": "Personal 5G Hotspot",
            "network_type": "PERSONAL_CELLULAR"
        },
        "selfie_image_base64": "data:image/jpeg;base64,sample_clock_out_selfie_base64_data",
        "face_liveness_passed": True
    }
    status, clock_out_res = http_post(f"{BASE_URL}/attendance/clock-out", clock_out_payload, auth_headers)
    assert status == 200, f"Clock out failed: {clock_out_res}"
    print(f"  4. Clock-Out via Personal Internet Successful! Shift Hours: {clock_out_res['total_shift_hours']}, Network: {clock_out_res['network_type']}")

    print("ALL CELLULAR ATTENDANCE VERIFICATIONS PASSED!")

if __name__ == "__main__":
    test_attendance_flow()
