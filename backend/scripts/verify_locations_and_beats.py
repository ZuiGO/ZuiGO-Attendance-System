import urllib.request
import json

BASE = "http://127.0.0.1:8000/api/v1"

def req(method, path, data=None, token=None):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Tenant-ID": "6c9e4114-81b7-44cd-815b-549487252608"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    with urllib.request.urlopen(r) as res:
        return res.getcode(), json.loads(res.read().decode())

def run():
    print("Testing Locations & Beats API endpoints...")
    _, login = req("POST", "/auth/login", {"email": "jayesh@zuigo.ai", "password": "password123", "tenant_id": "zuigo"})
    token = login["access_token"]

    # 1. Offices
    code, offices = req("GET", "/admin/offices", token=token)
    print(f"[PASS] GET /admin/offices: HTTP {code}, count: {len(offices)}")

    code, new_off = req("POST", "/admin/offices", {
        "name": "DLF Horizon Cyber Branch",
        "address": "Horizon Center, Golf Course Rd",
        "latitude": 28.4595,
        "longitude": 77.0725,
        "allowed_radius_meters": 80,
        "allowed_bssid_list": ["11:22:33:44:55:66"]
    }, token=token)
    office_id = new_off["id"]
    print(f"[PASS] POST /admin/offices: HTTP {code}, created: {new_off['name']} ({office_id})")

    code, _ = req("DELETE", f"/admin/offices/{office_id}", token=token)
    print(f"[PASS] DELETE /admin/offices: HTTP {code}, deactivated: {office_id}")

    # 2. Destinations
    code, dests = req("GET", "/admin/destinations", token=token)
    print(f"[PASS] GET /admin/destinations: HTTP {code}, count: {len(dests)}")

    code, new_dest = req("POST", "/admin/destinations", {
        "name": "Max Healthcare Super Speciality",
        "client_type": "HOSPITAL",
        "contact_person": "Dr. Alok Verma",
        "contact_phone": "+919811122233",
        "latitude": 28.5285,
        "longitude": 77.2185,
        "geofence_radius_meters": 75,
        "min_dwell_minutes": 30
    }, token=token)
    dest_id = new_dest["id"]
    print(f"[PASS] POST /admin/destinations: HTTP {code}, created: {new_dest['name']} ({dest_id})")

    code, _ = req("DELETE", f"/admin/destinations/{dest_id}", token=token)
    print(f"[PASS] DELETE /admin/destinations: HTTP {code}, deactivated: {dest_id}")

    # 3. Field beats
    code, beats = req("GET", "/admin/field-beats", token=token)
    print(f"[PASS] GET /admin/field-beats: HTTP {code}, count: {len(beats)}")
    for b in beats[:3]:
        safe_otp = b['otp_status'].encode('ascii', 'ignore').decode('ascii')
        print(f"   Beat: {b['destination_name']} | Staff: {b['employee_name']} | Geofence: {b['geofence_status']} | OTP: {safe_otp}")

    print("ALL LOCATION & BEAT TESTS PASSED!")

if __name__ == "__main__":
    run()
