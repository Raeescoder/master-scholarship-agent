from starlette.testclient import TestClient
from app import app

client = TestClient(app)

def test_document_review_and_plagiarism():
    print("[TEST] Testing Document Review & Plagiarism Checker...")

    # Sample SOP with intentional clichés to test detection
    cliche_sop = """
    Ever since I was a child, I have always been passionate about computer science. 
    In today's rapidly changing world, technology is evolving at an unprecedented pace, 
    and it goes without saying that knowledge is power. I am a very hardworking student 
    who wants to give back to my country. This Erasmus Mundus scholarship is a golden opportunity 
    and a stepping stone for my future career. During my undergraduate studies at National University, 
    I developed an AI diagnostic model that achieved 94.2% accuracy across 12,000 medical image scans. 
    I published 1 IEEE conference paper and managed a student hackathon team of 5 engineers. 
    I wish to pursue my Master's degree in Europe to establish an open-source health-tech institute.
    """

    # 1. Test /api/tools/plagiarism-check
    payload = {
        "content": cliche_sop,
        "doc_type": "sop",
        "scholarship_id": "erasmus_mundus"
    }

    r = client.post("/api/tools/plagiarism-check", json=payload)
    assert r.status_code == 200, f"Endpoint failed: {r.text}"
    data = r.json()

    assert data["word_count"] > 50
    assert data["cliche_count"] >= 3, f"Expected at least 3 clichés, found {data['cliche_count']}"
    assert len(data["highlighted_snippets"]) >= 3
    assert len(data["rewrite_suggestions"]) >= 2
    assert "Originality Index" in data["plagiarism_analysis"]
    print(f"[PASS] Plagiarism & Cliché Checker passed. Detected {data['cliche_count']} clichés, Originality Score: {data['originality_score']}%, Overall Score: {data['overall_score']}%.")

    # 2. Test /api/tools/review-document with CV
    cv_text = """
    Alex Chen | Full Stack AI Researcher
    Education: B.Tech Computer Science, GPA: 3.8/4.0
    Publications: 1 IEEE Conference paper on Deep Learning (2025)
    Experience: 2 years software engineer at TechCorp, scaled microservices to 500,000 monthly users.
    Skills: Python, PyTorch, FastAPI, Docker, Kubernetes.
    """
    r_cv = client.post("/api/tools/review-document", json={"content": cv_text, "doc_type": "cv"})
    assert r_cv.status_code == 200
    cv_data = r_cv.json()
    assert cv_data["overall_score"] > 50
    print(f"[PASS] CV Review passed. Score: {cv_data['overall_score']}%, Verdict: {cv_data['committee_verdict']}")

    print("\n[SUCCESS] DOCUMENT REVIEW & PLAGIARISM AGENT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_document_review_and_plagiarism()
