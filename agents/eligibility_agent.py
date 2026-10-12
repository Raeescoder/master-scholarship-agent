from typing import Dict, Any, List
from models import UserProfile, MatchEvaluation
from data.scholarships_db import SCHOLARSHIPS_DATABASE
from agents.gemini_client import gemini_client

class EligibilityAgent:
    """
    Performs multi-criteria evaluation of an applicant against specific scholarship requirements,
    calculates weighted scores, identifies disqualification risks, and gives tactical fixes.
    """

    def evaluate(self, profile: UserProfile, scholarship_id: str, profile_summary: Dict[str, Any]) -> MatchEvaluation:
        # Find scholarship in DB
        scholarship = next((s for s in SCHOLARSHIPS_DATABASE if s["id"] == scholarship_id), None)
        if not scholarship:
            # Fallback placeholder if custom ID
            scholarship = {
                "id": scholarship_id,
                "name": scholarship_id.replace("_", " ").title(),
                "min_gpa_requirement": "3.0 / 4.0",
                "work_exp_requirement": "None specified",
                "language_requirement": "IELTS 6.5+",
                "eligible_nationalities": "All Nationalities",
                "target_fields": ["All Fields"]
            }

        normalized_gpa = profile_summary.get("normalized_gpa", profile.gpa)
        work_years = profile.work_experience_years
        has_english = profile_summary.get("has_english_proof", False)

        checklist = {
            "nationality_eligible": True,
            "academic_qualification": True,
            "work_experience_met": True,
            "language_readiness": True,
            "field_alignment": True
        }

        strengths: List[str] = []
        obstacles: List[str] = []

        # 1. GPA Evaluation (Weight: 25)
        gpa_score = 25
        if "top 10%" in scholarship["min_gpa_requirement"].lower() or "3.8" in scholarship["min_gpa_requirement"]:
            if normalized_gpa >= 3.7:
                strengths.append(f"Outstanding GPA ({normalized_gpa}/4.0) satisfies the top-percentile academic criterion.")
            elif normalized_gpa >= 3.3:
                gpa_score = 18
                obstacles.append(f"Your GPA ({normalized_gpa}) is competitive, but this award favors top 5-10% of class. Highlight research/projects.")
            else:
                gpa_score = 10
                checklist["academic_qualification"] = False
                obstacles.append(f"High risk: Minimum typical GPA is 3.5-3.8. Your normalized GPA ({normalized_gpa}) needs strong compensating factors.")
        else:
            if normalized_gpa >= 3.3:
                strengths.append(f"Solid academic standing ({normalized_gpa}/4.0) easily meets the baseline benchmark.")
            elif normalized_gpa >= 2.8:
                gpa_score = 18
                strengths.append(f"GPA ({normalized_gpa}/4.0) clears minimum requirements; focus heavily on your Statement of Purpose.")
            else:
                gpa_score = 12
                obstacles.append(f"GPA ({normalized_gpa}/4.0) is near lower cutoff; emphasize work projects or publications.")

        # 2. Work Experience Evaluation (Weight: 25)
        work_score = 25
        needs_strict_exp = any(phrase in scholarship["work_exp_requirement"].lower() for phrase in ["strict", "2 years", "3,000 hours", "minimum of 2 years"])
        if needs_strict_exp:
            if work_years >= 2.0:
                strengths.append(f"You have {work_years} years of work experience, successfully satisfying the 2-year mandatory rule.")
            else:
                work_score = 5
                checklist["work_experience_met"] = False
                obstacles.append(f"Strict Disqualification Alert: Requires at least 2 full years (2,800+ hours). You have {work_years} yrs.")
        else:
            if work_years > 0:
                strengths.append(f"{work_years} years of experience provides an advantage in the holistic review.")
            else:
                work_score = 20
                strengths.append("This program welcomes fresh graduates without penalizing lack of professional work years.")

        # 3. Language Evaluation (Weight: 20)
        lang_score = 20
        if not has_english:
            lang_score = 12
            checklist["language_readiness"] = False
            obstacles.append("English test result pending: Most candidates must present IELTS 6.5+ or TOEFL 85+ by deadline.")
        else:
            strengths.append(f"Language requirement validated: {profile.english_test}.")

        # 4. Field & Destination Fit (Weight: 20)
        field_score = 20
        target_fields = [f.lower() for f in scholarship.get("target_fields", [])]
        user_field = profile.target_degree_field.lower()
        if "all fields" in target_fields or any(w in user_field for f in target_fields for w in f.split()):
            strengths.append(f"Your target program '{profile.target_degree_field}' directly matches sponsored subject domains.")
        else:
            field_score = 14
            obstacles.append(f"Verify that your specific degree curriculum qualifies under '{', '.join(scholarship.get('target_fields', [])[:3])}'.")

        # 5. Nationality & Quota (Weight: 10)
        nat_score = 10
        strengths.append(f"Applicants holding {profile.nationality} citizenship are eligible under program guidelines.")

        total_score = gpa_score + work_score + lang_score + field_score + nat_score
        total_score = max(15, min(99, total_score))

        # Verdict
        if total_score >= 85 and all(checklist.values()):
            verdict = "Highly Recommended Match"
        elif total_score >= 70 and checklist["work_experience_met"]:
            verdict = "Competitive Match"
        elif not checklist["work_experience_met"] and needs_strict_exp:
            verdict = "High Ineligibility Risk (Missing Work Experience)"
        elif total_score >= 50:
            verdict = "Moderate Match (Reach Program)"
        else:
            verdict = "Low Alignment / Not Advised"

        # Key tactical advice
        if not checklist["work_experience_met"]:
            key_advice = f"Do not apply this year unless your internships/volunteering can be officially certified as 2,800+ hours. Redirect effort to Erasmus Mundus or MEXT instead."
        elif not checklist["language_readiness"]:
            key_advice = f"Your profile is viable! Immediately book an IELTS or TOEFL exam to obtain official score report before the application deadline."
        elif normalized_gpa >= 3.6:
            key_advice = f"You are a strong candidate. Focus 80% of your effort on crafting a stellar, tailored Statement of Purpose highlighting societal impact and research capability."
        else:
            key_advice = f"Frame your undergraduate story around practical skills, senior design thesis, and clear post-graduation contribution goals to outshine higher-GPA applicants."

        # If Gemini is active, enrich with customized AI evaluation
        if gemini_client.has_valid_key():
            prompt = f"""
Act as a scholarship selection committee chair evaluating this candidate:
Applicant:
- Nationality: {profile.nationality}
- Desired Subject: {profile.target_degree_field} (Undergrad: {profile.bachelor_field})
- Normalized GPA: {normalized_gpa}/4.0
- Work Experience: {work_years} years
- Language: {profile.english_test}

Scholarship:
- Name: {scholarship['name']}
- Requirement: {scholarship.get('min_gpa_requirement')}; Exp: {scholarship.get('work_exp_requirement')}

Give 2 sentences of brutally honest advice on how this applicant can maximize their chances of winning.
"""
            ai_eval = gemini_client.generate_text(prompt)
            if ai_eval:
                key_advice = f"{key_advice} Selection Committee Tip: {ai_eval.strip()}"

        return MatchEvaluation(
            scholarship_id=scholarship_id,
            scholarship_name=scholarship["name"],
            match_score=total_score,
            verdict=verdict,
            strengths=strengths,
            potential_obstacles=obstacles,
            checklist=checklist,
            key_advice=key_advice
        )

eligibility_agent = EligibilityAgent()
