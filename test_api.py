from starlette.testclient import TestClient
from app import app

client = TestClient(app)

def test_endpoints():
    print("[TEST] Testing REST Endpoints via TestClient...")

    # 1. Health
    r = client.get("/api/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    data = r.json()
    assert data["status"] == "healthy"
    print(f"[PASS] Health check OK, {data['scholarships_indexed']} scholarships indexed.")

    # 2. Scholarships list
    r = client.get("/api/scholarships")
    assert r.status_code == 200
    assert len(r.json()) >= 15
    print(f"[PASS] GET /api/scholarships returned {len(r.json())} items.")

    # 3. Agent Discover
    profile_payload = {
        "full_name": "Maria Silva",
        "nationality": "Brazil",
        "bachelor_field": "Electrical Engineering",
        "gpa": 8.5,
        "gpa_scale": 10.0,
        "target_degree_field": "Renewable Energy & Power Systems",
        "target_countries": ["Germany", "Sweden"],
        "work_experience_years": 2.0,
        "english_test": "TOEFL 98",
        "funding_type_needed": "Fully Funded"
    }
    r = client.post("/api/agent/discover", json=profile_payload)
    assert r.status_code == 200, f"Discovery endpoint failed: {r.text}"
    disc_data = r.json()
    assert "matched_scholarships" in disc_data
    assert len(disc_data["matched_scholarships"]) > 0
    print(f"[PASS] POST /api/agent/discover returned {len(disc_data['matched_scholarships'])} matched scholarships.")

    # 4. Agent Roadmap
    rm_payload = {
        "profile": profile_payload,
        "scholarship_id": "erasmus_mundus"
    }
    r = client.post("/api/agent/roadmap", json=rm_payload)
    assert r.status_code == 200
    rm_data = r.json()
    assert "timeline_steps" in rm_data
    print(f"[PASS] POST /api/agent/roadmap returned {len(rm_data['timeline_steps'])} timeline steps.")

    # 5. Agent Chat
    chat_payload = {
        "profile": profile_payload,
        "messages": [{"role": "user", "content": "How do I explain my GPA in the SOP?"}],
        "selected_scholarship_id": "erasmus_mundus"
    }
    r = client.post("/api/agent/chat", json=chat_payload)
    assert r.status_code == 200
    chat_data = r.json()
    assert "reply" in chat_data and len(chat_data["reply"]) > 20
    print(f"[PASS] POST /api/agent/chat returned strategic advice.")

    # 6. Static Index
    r = client.get("/")
    assert r.status_code == 200
    assert "ScholarAI" in r.text
    print("[PASS] GET / serves index.html properly.")

    print("\n[SUCCESS] ALL REST API ENDPOINTS VALIDATED SUCCESSFULLY!")

if __name__ == "__main__":
    test_endpoints()
