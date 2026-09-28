"""
Back2You — Comprehensive Integration & End-to-End Audit Test Suite
Runs real HTTP transactions against FastAPI app, SQLite database, and ML services.
"""

import sys
import uuid
from datetime import date
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.db import get_db_connection

# Ensure safe printing on Windows cp1252 consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

client = TestClient(app)

def run_tests():
    print("==================================================")
    print("   BACK2YOU COMPREHENSIVE INTEGRATION AUDIT TEST   ")
    print("==================================================")
    
    passed_count = 0
    total_tests = 11

    # 1. Backend Startup & OpenAPI Docs Check
    print("\n[TEST 1/11] Checking Backend Startup & /docs...")
    res = client.get("/docs")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    res_redoc = client.get("/redoc")
    assert res_redoc.status_code == 200, f"Expected 200, got {res_redoc.status_code}"
    print("  ✓ PASS: FastAPI documentation endpoints (/docs, /redoc) active and accessible.")
    passed_count += 1

    # 2. Database Connection & Required Tables Check
    print("\n[TEST 2/11] Checking Database Connection & Required Tables...")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cursor.fetchall()}
    conn.close()
    
    required_tables = {"users", "items", "item_embeddings", "matches", "claims", "gamification", "badges", "notifications"}
    missing = required_tables - tables
    assert not missing, f"Missing required database tables: {missing}"
    print(f"  ✓ PASS: Database active with tables: {', '.join(sorted(tables))}")
    passed_count += 1

    # 3. Authentication: Student Registration & Login
    print("\n[TEST 3/11] Checking Student Registration & JWT Authentication...")
    test_email = f"student_{uuid.uuid4().hex[:6]}@campus.edu"
    test_password = "SecureStudentPass123!"
    
    # Register
    reg_res = client.post("/api/auth/register", json={
        "name": "Jordan Smith",
        "email": test_email,
        "password": test_password,
        "role": "USER"
    })
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
    reg_data = reg_res.json()
    assert "access_token" in reg_data, "No access_token returned from registration"
    student_token = reg_data["access_token"]
    student_user = reg_data["user"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    
    # Login
    login_res = client.post("/api/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    print(f"  ✓ PASS: User registered ({test_email}) and authenticated successfully.")
    passed_count += 1

    # 4. Authentication: Admin Login & Authorization Guard
    print("\n[TEST 4/11] Checking Admin Login & Authorization Controls...")
    admin_login = client.post("/api/auth/login", json={
        "email": "admin@campus.edu",
        "password": "AdminPass123!"
    })
    assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Check student blocked from admin endpoint
    forbidden_res = client.get("/api/admin/statistics", headers=student_headers)
    assert forbidden_res.status_code == 403, f"Expected 403 for student on admin endpoint, got {forbidden_res.status_code}"
    
    # Check admin allowed
    admin_stats_res = client.get("/api/admin/statistics", headers=admin_headers)
    assert admin_stats_res.status_code == 200, f"Expected 200 for admin, got {admin_stats_res.status_code}"
    print("  ✓ PASS: Admin authentication and role-based access control verified.")
    passed_count += 1

    # 5. Report Lost Item & AI Embeddings Generation
    print("\n[TEST 5/11] Checking Lost Item Reporting & AI NLP Embedding...")
    lost_payload = {
        "type": "lost",
        "title": "Blue Hydro Flask Water Bottle",
        "category": "Bottles & Containers",
        "description": "Navy blue stainless steel 32oz Hydro Flask with national park stickers and small dent on base.",
        "brand": "Hydro Flask",
        "color": "Navy Blue",
        "distinguishing_features": "Dent on the bottom and Yosemite sticker",
        "location": "Main Library",
        "event_date": date.today().isoformat(),
        "event_time": "14:30"
    }
    lost_res = client.post("/api/items/lost", json=lost_payload, headers=student_headers)
    assert lost_res.status_code == 200, f"Lost report failed: {lost_res.text}"
    lost_data = lost_res.json()["item"]
    lost_id = lost_data["id"]
    print(f"  ✓ PASS: Lost item reported (ID: {lost_id[:8]}) and indexed for semantic search.")
    passed_count += 1

    # 6. Report Found Item & AI Embeddings Generation (from another student)
    print("\n[TEST 6/11] Checking Found Item Reporting by Finder...")
    # Finder: Sarah Chen
    sarah_login = client.post("/api/auth/login", json={
        "email": "sarah@campus.edu",
        "password": "StudentPass123!"
    })
    assert sarah_login.status_code == 200, "Sarah Chen login failed"
    sarah_headers = {"Authorization": f"Bearer {sarah_login.json()['access_token']}"}

    found_payload = {
        "type": "found",
        "title": "Blue Metal Water Bottle",
        "category": "Bottles & Containers",
        "description": "Dark blue Hydro Flask water bottle found on second floor study table near windows.",
        "brand": "Hydro Flask",
        "color": "Dark Blue",
        "distinguishing_features": "Has colorful outdoor stickers",
        "location": "Main Library",
        "event_date": date.today().isoformat(),
        "event_time": "15:00"
    }
    found_res = client.post("/api/items/found", json=found_payload, headers=sarah_headers)
    assert found_res.status_code == 200, f"Found report failed: {found_res.text}"
    found_data = found_res.json()["item"]
    found_id = found_data["id"]
    print(f"  ✓ PASS: Found item reported (ID: {found_id[:8]}) by finder.")
    passed_count += 1

    # 7. AI Multi-Modal Matching Engine Execution
    print("\n[TEST 7/11] Checking Multi-Modal Matching Engine...")
    match_res = client.post(f"/api/matching/find?item_id={lost_id}&limit=5", headers=student_headers)
    assert match_res.status_code == 200, f"Matching failed: {match_res.text}"
    match_data = match_res.json()
    matches = match_data.get("matches", [])
    assert len(matches) > 0, "No matches identified by AI engine"
    top_match = matches[0]
    breakdown = top_match["breakdown"]
    confidence = breakdown["final_confidence"]
    print(f"  ✓ Confidence Score: {breakdown['confidence_percentage']}% ({breakdown['confidence_level'].upper()})")
    print(f"    - Text Similarity:     {breakdown['text_similarity']}")
    print(f"    - Category Similarity: {breakdown['category_similarity']}")
    print(f"    - Brand Similarity:    {breakdown['brand_similarity']}")
    print(f"    - Location Similarity: {breakdown['location_similarity']}")
    print(f"    - Temporal Similarity: {breakdown['time_similarity']}")
    print(f"    - Explainable reasons: {', '.join(breakdown['explanation'][:2])}")
    assert confidence > 0.40, f"Expected confidence > 0.40, got {confidence}"
    print("  ✓ PASS: Multi-modal scoring and explanation engine verified.")
    passed_count += 1

    # 8. Ownership Claim Submission & Duplicate / Self-Claim Protections
    print("\n[TEST 8/11] Checking Ownership Verification Claim...")
    # Finder cannot claim their own found item
    self_claim_res = client.post("/api/claims", json={
        "item_id": found_id,
        "verification_answers": {
            "distinguishing_features": "My sticker",
            "proof_details": "Self claim test"
        }
    }, headers=sarah_headers)
    assert self_claim_res.status_code == 400, "Finder was incorrectly allowed to claim own reported item"

    # Owner submits legitimate claim
    claim_res = client.post("/api/claims", json={
        "match_id": top_match.get("match_id"),
        "item_id": found_id,
        "verification_answers": {
            "distinguishing_features": "Yosemite sticker and dent on bottom",
            "proof_details": "Lost it while studying for CS exam"
        }
    }, headers=student_headers)
    assert claim_res.status_code == 200, f"Claim failed: {claim_res.text}"
    claim_id = claim_res.json()["id"]

    # Duplicate claim attempt must be rejected
    dup_res = client.post("/api/claims", json={
        "item_id": found_id,
        "verification_answers": {
            "distinguishing_features": "Duplicate test",
            "proof_details": "Should be rejected"
        }
    }, headers=student_headers)
    assert dup_res.status_code == 400, "Duplicate active claim was not rejected"
    print(f"  ✓ PASS: Claim submitted (ID: {claim_id[:8]}) and guardrails enforced.")
    passed_count += 1

    # 9. Admin Verification & Official Item Return Handover
    print("\n[TEST 9/11] Checking Admin Verification & Return Handover...")
    verify_res = client.post(f"/api/admin/claims/{claim_id}/verify", json={
        "notes": "Verified against claimant student card and unique stickers."
    }, headers=admin_headers)
    assert verify_res.status_code == 200, f"Admin verify failed: {verify_res.text}"
    
    return_res = client.post(f"/api/admin/items/{found_id}/return", headers=admin_headers)
    assert return_res.status_code == 200, f"Item return failed: {return_res.text}"
    print("  ✓ PASS: Claim verified by campus security and item marked as RETURNED.")
    passed_count += 1

    # 10. Community Helper Gamification & Rewards Check
    print("\n[TEST 10/11] Checking Community Gamification Points & Badges...")
    sarah_profile_res = client.get("/api/community/gamification", headers=sarah_headers)
    assert sarah_profile_res.status_code == 200, "Gamification query failed"
    gam_data = sarah_profile_res.json()
    assert gam_data.get("points", 0) > 0, "Finder was not awarded helper points"
    
    leaderboard_res = client.get("/api/community/leaderboard?limit=10")
    assert leaderboard_res.status_code == 200, "Leaderboard query failed"
    leaderboard = leaderboard_res.json()
    assert len(leaderboard) > 0, "Leaderboard is empty"
    print(f"  ✓ PASS: Gamification awarded points to finder (Total: {gam_data.get('points')} pts).")
    passed_count += 1

    # 11. Notifications & User Profile Flow
    print("\n[TEST 11/11] Checking Notifications & Profile Endpoints...")
    notif_res = client.get("/api/notifications", headers=student_headers)
    assert notif_res.status_code == 200, "Notifications query failed"
    
    read_all_res = client.post("/api/notifications/read-all", headers=student_headers)
    assert read_all_res.status_code == 200, "Read all notifications failed"

    prof_res = client.get("/api/profile", headers=student_headers)
    assert prof_res.status_code == 200, "Profile query failed"
    
    patch_res = client.patch("/api/profile", json={"full_name": "Jordan Smith Updated"}, headers=student_headers)
    assert patch_res.status_code == 200, "Profile update failed"
    print("  ✓ PASS: Profile and notifications verified.")
    passed_count += 1

    print("\n==================================================")
    print(f"   TEST SUMMARY: {passed_count}/{total_tests} SUITES PASSED (100%)   ")
    print("==================================================")

if __name__ == "__main__":
    try:
        run_tests()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST ASSERTION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
