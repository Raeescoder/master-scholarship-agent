import sys
from models import UserProfile
from agents.profile_agent import profile_agent
from agents.discovery_agent import discovery_agent
from agents.eligibility_agent import eligibility_agent
from agents.roadmap_agent import roadmap_agent
from agents.advisor_agent import advisor_agent
from models import ChatMessage

def run_smoke_test():
    print("Testing ScholarAI Agent Pipeline...")

    # 1. Test profile creation & analysis
    profile = UserProfile(
        full_name="Test Applicant",
        nationality="India",
        bachelor_field="Computer Science",
        gpa=3.8,
        gpa_scale=4.0,
        target_degree_field="Artificial Intelligence",
        target_countries=["Germany", "Europe", "UK"],
        work_experience_years=1.5,
        english_test="IELTS 7.5",
        funding_type_needed="Fully Funded"
    )
    
    summary = profile_agent.analyze_profile(profile)
    assert summary["normalized_gpa"] == 3.8
    assert "Tier 1" in summary["academic_tier"]
    print("[PASS] ProfileAgent test passed.")

    # 2. Test Discovery Agent
    discovery = discovery_agent.discover_scholarships(profile, summary)
    matches = discovery["matched_scholarships"]
    assert len(matches) > 0
    print(f"[PASS] DiscoveryAgent test passed: {len(matches)} scholarships found.")

    # 3. Test Eligibility Agent
    top_id = matches[0]["id"]
    eval_res = eligibility_agent.evaluate(profile, top_id, summary)
    assert eval_res.match_score >= 0 and eval_res.match_score <= 100
    print(f"[PASS] EligibilityAgent test passed: Evaluated '{eval_res.scholarship_name}', score={eval_res.match_score}.")

    # 4. Test Roadmap Agent
    roadmap = roadmap_agent.generate_roadmap(profile, top_id)
    assert len(roadmap.timeline_steps) >= 4
    assert "hook_section" in roadmap.sop_framework
    print(f"[PASS] RoadmapAgent test passed: Generated roadmap with {len(roadmap.timeline_steps)} phases.")

    # 5. Test Advisor Agent Chat
    messages = [ChatMessage(role="user", content="How do I structure my motivation letter?")]
    reply = advisor_agent.reply(messages, profile=profile, scholarship_id=top_id)
    assert len(reply) > 50
    print(f"[PASS] AdvisorAgent test passed: Generated {len(reply)} chars reply.")

    print("\n[SUCCESS] ALL AGENT MODULES PASSED SMOKE TESTS SUCCESSFULLY!")

if __name__ == "__main__":
    run_smoke_test()
