import uuid
from starlette.testclient import TestClient
from app import app

client = TestClient(app)

def test_auth_pipeline():
    print("[TEST] Running User Account & Auth Test Suite...")

    # Unique test email
    unique_email = f"student_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "securepassword123"

    # 1. Register
    reg_payload = {
        "email": unique_email,
        "password": pwd,
        "full_name": "Test Scholar",
        "nationality": "Ghana"
    }
    r = client.post("/api/auth/register", json=reg_payload)
    assert r.status_code == 200, f"Register failed: {r.text}"
    data = r.json()
    assert data["success"] is True
    assert "token" in data
    token = data["token"]
    print(f"[PASS] User registered successfully with email: {unique_email}")

    # 2. Duplicate registration protection
    r = client.post("/api/auth/register", json=reg_payload)
    assert r.status_code == 400
    print("[PASS] Duplicate registration rejected.")

    # 3. Login
    login_payload = {
        "email": unique_email,
        "password": pwd
    }
    r = client.post("/api/auth/login", json=login_payload)
    assert r.status_code == 200
    login_data = r.json()
    assert "token" in login_data
    auth_token = login_data["token"]
    print("[PASS] User login succeeded.")

    # 4. Verify /api/auth/me
    headers = {"Authorization": f"Bearer {auth_token}"}
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    me_data = r.json()
    assert me_data["user"]["email"] == unique_email
    print(f"[PASS] /api/auth/me verified user: {me_data['user']['full_name']}")

    # 5. Save & Fetch Profile
    prof_payload = {
        "full_name": "Test Scholar Updated",
        "nationality": "Ghana",
        "bachelor_field": "Computer Engineering",
        "gpa": 3.85,
        "gpa_scale": 4.0,
        "target_degree_field": "Robotics & Autonomous Systems",
        "target_countries": ["Germany", "Japan"],
        "work_experience_years": 2.0,
        "english_test": "IELTS 7.5",
        "funding_type_needed": "Fully Funded"
    }
    r = client.post("/api/user/profile", json=prof_payload, headers=headers)
    assert r.status_code == 200
    print("[PASS] User profile saved to database.")

    r = client.get("/api/user/profile", headers=headers)
    assert r.status_code == 200
    saved_prof = r.json()["profile"]
    assert saved_prof["bachelor_field"] == "Computer Engineering"
    assert saved_prof["gpa"] == 3.85
    print("[PASS] User profile retrieved from database.")

    # 6. Bookmarking
    r = client.post("/api/user/bookmarks/toggle", json={"scholarship_id": "erasmus_mundus"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["bookmarked"] is True
    print("[PASS] Bookmark toggled ON.")

    r = client.get("/api/user/bookmarks", headers=headers)
    assert r.status_code == 200
    assert "erasmus_mundus" in r.json()["bookmarks"]
    print("[PASS] User bookmarks retrieved successfully.")

    # 7. Logout
    r = client.post("/api/auth/logout", headers=headers)
    assert r.status_code == 200
    print("[PASS] User logged out.")

    print("\n[SUCCESS] ALL AUTHENTICATION TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_auth_pipeline()
