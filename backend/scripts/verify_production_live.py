import time
import uuid
import requests

PROD_URL = "https://bhashashield-api.onrender.com"

def wait_for_deployment(max_wait_seconds=240, poll_interval=10):
    print(f"Polling {PROD_URL} for latest release deployment...")
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        try:
            r = requests.get(PROD_URL, headers={"Accept": "text/html"}, timeout=10)
            if r.status_code == 200:
                # Check for new bundle or CSV endpoint to confirm new code rollout
                if "index-DuUs1lA3.js" in r.text:
                    print("--> New deployment (bundle index-DuUs1lA3.js) is LIVE!")
                    return True
                else:
                    print(f"[{int(time.time() - start_time)}s] Service responsive; waiting for new bundle rollout...")
            else:
                print(f"[{int(time.time() - start_time)}s] Service returned {r.status_code}")
        except Exception as e:
            print(f"[{int(time.time() - start_time)}s] Connection error: {e}")
        
        time.sleep(poll_interval)
    
    print("Wait timeout reached. Testing current live instance...")
    return False

def run_live_tests():
    print("=" * 60)
    print("STARTING LIVE PRODUCTION VERIFICATION")
    print(f"Target: {PROD_URL}")
    print("=" * 60)

    # 1. Health & Database Diagnostic
    health_resp = requests.get(f"{PROD_URL}/v1/health", timeout=10)
    health = health_resp.json()
    print("\n[1] LIVE HEALTH & DATABASE CONFIGURATION:")
    print(f"  Overall Status:            {health.get('status')}")
    print(f"  Git Commit:                {health.get('git_commit')}")
    print(f"  Model Engine Status:       {health.get('model_status')}")
    db_info = health.get("database", {})
    print(f"  Database Backend:          {db_info.get('backend')}")
    print(f"  DATABASE_URL Configured:   {db_info.get('database_url_configured')}")
    print(f"  Persistence Mode:          {db_info.get('persistence_mode')}")
    print(f"  Total Scans Recorded:      {db_info.get('total_scans_recorded')}")

    # 2. CORS Preflight & Environment Separation
    print("\n[2] CORS PREFLIGHT & ORIGIN RESTRICTION:")
    allowed_origin = "https://bhashashield-api.onrender.com"
    r_cors_allowed = requests.options(
        f"{PROD_URL}/v1/analyze",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        },
        timeout=10
    )
    cors_hdr = r_cors_allowed.headers.get("access-control-allow-origin")
    print(f"  Allowed Origin ({allowed_origin}): Status={r_cors_allowed.status_code}, Allow-Origin={cors_hdr}")
    
    unauthorized_origin = "https://malicious-scam-site.attacker.com"
    r_cors_blocked = requests.options(
        f"{PROD_URL}/v1/analyze",
        headers={
            "Origin": unauthorized_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        },
        timeout=10
    )
    cors_blocked_hdr = r_cors_blocked.headers.get("access-control-allow-origin")
    print(f"  Unauthorized Origin ({unauthorized_origin}): Status={r_cors_blocked.status_code}, Allow-Origin={cors_blocked_hdr}")

    # Verify localhost origin is rejected in production
    r_cors_localhost = requests.options(
        f"{PROD_URL}/v1/analyze",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        },
        timeout=10
    )
    print(f"  Localhost in Production (http://localhost:5173): Status={r_cors_localhost.status_code}, Allow-Origin={r_cors_localhost.headers.get('access-control-allow-origin')}")

    # 3. User Authentication Flow & Password Complexity
    print("\n[3] USER REGISTRATION, COMPLEXITY & AUTHENTICATION:")
    u_suffix = uuid.uuid4().hex[:6]
    user_a = f"sec_user_a_{u_suffix}"
    pass_a = "StrongPassA123!"

    # Complexity rejection test
    r_weak = requests.post(
        f"{PROD_URL}/v1/auth/register",
        json={"username": f"weak_{u_suffix}", "password": "onlyletters"},
        timeout=10
    )
    print(f"  Password Complexity Enforcement: Status={r_weak.status_code} (Expected 400)")
    
    r_reg_a = requests.post(f"{PROD_URL}/v1/auth/register", json={"username": user_a, "password": pass_a}, timeout=10)
    print(f"  Register User A ({user_a}): Status={r_reg_a.status_code}")
    assert r_reg_a.status_code == 200, f"Registration failed: {r_reg_a.text}"
    token_a = r_reg_a.json()["access_token"]
    user_a_id = r_reg_a.json()["user"]["id"]
    print(f"    User A ID: {user_a_id}, Token received: {token_a[:15]}...")

    # Duplicate registration prevention
    r_dup = requests.post(f"{PROD_URL}/v1/auth/register", json={"username": user_a, "password": pass_a}, timeout=10)
    print(f"  Duplicate Registration Attempt: Status={r_dup.status_code} (Expected 409)")

    # User B
    user_b = f"sec_user_b_{u_suffix}"
    pass_b = "StrongPassB456!"
    r_reg_b = requests.post(f"{PROD_URL}/v1/auth/register", json={"username": user_b, "password": pass_b}, timeout=10)
    print(f"  Register User B ({user_b}): Status={r_reg_b.status_code}")
    token_b = r_reg_b.json()["access_token"]
    user_b_id = r_reg_b.json()["user"]["id"]

    # Verify /me endpoint
    r_me = requests.get(f"{PROD_URL}/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"}, timeout=10)
    print(f"  Verify Token A via /v1/auth/me: Status={r_me.status_code}, Username={r_me.json().get('username')}")

    # 4. Multi-User Scan Isolation
    print("\n[4] MULTI-USER SCAN DATA ISOLATION:")
    scan_text_a = f"User A confidential scan query {u_suffix}"
    r_scan_a = requests.post(
        f"{PROD_URL}/v1/analyze",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"text": scan_text_a, "save_to_history": True},
        timeout=10
    )
    print(f"  User A performs scan: Status={r_scan_a.status_code}")
    scan_a_id = r_scan_a.json()["scan_id"]

    scan_text_b = f"User B isolated internal prompt {u_suffix}"
    r_scan_b = requests.post(
        f"{PROD_URL}/v1/analyze",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"text": scan_text_b, "save_to_history": True},
        timeout=10
    )
    print(f"  User B performs scan: Status={r_scan_b.status_code}")
    scan_b_id = r_scan_b.json()["scan_id"]

    # Check User A scans
    scans_for_a = requests.get(f"{PROD_URL}/v1/scans", headers={"Authorization": f"Bearer {token_a}"}, timeout=10).json()
    ids_for_a = [s["id"] for s in scans_for_a]
    print(f"  User A scans returned: {len(ids_for_a)} records")
    print(f"    Contains Scan A ({scan_a_id}): {scan_a_id in ids_for_a}")
    print(f"    Contains Scan B ({scan_b_id}): {scan_b_id in ids_for_a} (Expected: False - Isolated)")

    # Check User B scans
    scans_for_b = requests.get(f"{PROD_URL}/v1/scans", headers={"Authorization": f"Bearer {token_b}"}, timeout=10).json()
    ids_for_b = [s["id"] for s in scans_for_b]
    print(f"  User B scans returned: {len(ids_for_b)} records")
    print(f"    Contains Scan B ({scan_b_id}): {scan_b_id in ids_for_b}")
    print(f"    Contains Scan A ({scan_a_id}): {scan_a_id in ids_for_b} (Expected: False - Isolated)")

    # Check Anonymous scans
    anon_scans = requests.get(f"{PROD_URL}/v1/scans", timeout=10).json()
    anon_ids = [s["id"] for s in anon_scans]
    print(f"  Anonymous visitor scans returned: {len(anon_ids)} records")
    print(f"    Contains User A scan: {scan_a_id in anon_ids} (Expected: False - Private)")
    print(f"    Contains User B scan: {scan_b_id in anon_ids} (Expected: False - Private)")

    # 5. CSV Export Isolation
    print("\n[5] USER-ISOLATED CSV EXPORT:")
    r_csv_a = requests.get(f"{PROD_URL}/v1/scans/export/csv", headers={"Authorization": f"Bearer {token_a}"}, timeout=10)
    print(f"  User A CSV Export: Status={r_csv_a.status_code}")
    print(f"    Contains Scan A: {scan_a_id in r_csv_a.text}")
    print(f"    Contains Scan B: {scan_b_id in r_csv_a.text} (Expected: False - Isolated)")

    # 6. Server-Side Logout & Token Revocation
    print("\n[6] SERVER-SIDE LOGOUT & TOKEN REVOCATION:")
    r_logout = requests.post(f"{PROD_URL}/v1/auth/logout", headers={"Authorization": f"Bearer {token_a}"}, timeout=10)
    print(f"  User A Logout: Status={r_logout.status_code}")
    r_me_after_logout = requests.get(f"{PROD_URL}/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"}, timeout=10)
    print(f"  Access /v1/auth/me with Revoked Token: Status={r_me_after_logout.status_code} (Expected 401)")

    # 7. Cross-User Access & Deletion Security
    print("\n[7] CROSS-USER ACCESS & DELETION SECURITY:")
    r_del_unauth = requests.delete(
        f"{PROD_URL}/v1/scans/{scan_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        timeout=10
    )
    print(f"  User B attempts deleting User A's scan: Status={r_del_unauth.status_code} (Expected 404/403)")

    # 8. Frontend HTML & Asset Bundle Verification
    print("\n[8] FRONTEND ASSET & SPA SERVING:")
    r_front = requests.get(PROD_URL, headers={"Accept": "text/html"}, timeout=10)
    print(f"  GET / (Accept: text/html): Status={r_front.status_code}")
    print(f"    Contains BhashaShield Title: {'BhashaShield' in r_front.text}")
    print(f"    Contains Modern JS Bundle (index-DuUs1lA3.js): {'index-DuUs1lA3.js' in r_front.text}")

    print("\n" + "=" * 60)
    print("PRODUCTION VERIFICATION SUMMARY COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    wait_for_deployment()
    run_live_tests()
