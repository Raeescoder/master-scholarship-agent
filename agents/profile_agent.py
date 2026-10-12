from typing import Dict, Any
from models import UserProfile

class ProfileAgent:
    """
    Analyzes and structures candidate profile, normalizes GPAs,
    evaluates academic/professional strength, and extracts scholarship criteria.
    """

    def analyze_profile(self, profile: UserProfile) -> Dict[str, Any]:
        # Normalize GPA to 4.0 scale
        scale = profile.gpa_scale if profile.gpa_scale > 0 else 4.0
        normalized_gpa = round((profile.gpa / scale) * 4.0, 2)
        if normalized_gpa > 4.0:
            normalized_gpa = 4.0

        # Assess academic standing
        if normalized_gpa >= 3.7:
            academic_standing = "Outstanding / First Class Honours (Top 10%)"
            academic_tier = "Tier 1 - Highly Competitive"
        elif normalized_gpa >= 3.3:
            academic_standing = "Strong / Upper Second Class (2:1)"
            academic_tier = "Tier 2 - Very Competitive"
        elif normalized_gpa >= 2.8:
            academic_standing = "Good / Second Class Lower (2:2)"
            academic_tier = "Tier 3 - Eligible for holistic reviews"
        else:
            academic_standing = "Pass / Third Class - Requires strategic compensation"
            academic_tier = "Tier 4 - Needs targeted funding"

        # Assess professional experience
        work_years = profile.work_experience_years
        if work_years >= 2.0:
            work_status = f"{work_years} years - Meets strict professional quotas (Chevening, DAAD EPOS, Australia Awards)"
            work_eligible_for_pro = True
        else:
            work_status = f"{work_years} years - Best suited for academic, fresh graduate, or research scholarships (Erasmus, Turkiye Burslari, MEXT, GKS)"
            work_eligible_for_pro = False

        # Language status
        lang_str = profile.english_test or "None provided"
        has_english_proof = bool(profile.english_test and any(k in profile.english_test.lower() for k in ["ielts", "toefl", "duolingo", "pte", "native", "medium"]))

        # Build search query keywords
        search_keywords = [
            f"Master's scholarship {profile.target_degree_field}",
            f"Fully funded master {profile.nationality} students",
        ]
        for country in profile.target_countries:
            search_keywords.append(f"Government master scholarship {country}")

        strengths = []
        cautions = []

        if normalized_gpa >= 3.5:
            strengths.append(f"Strong academic GPA ({normalized_gpa}/4.0) opens doors to elite merit scholarships (Gates, ETH ESOP, Eiffel).")
        if work_eligible_for_pro:
            strengths.append(f"Sufficient work experience ({work_years} yrs) unlocks high-paying leadership awards (Chevening, DAAD EPOS).")
        if profile.research_experience:
            strengths.append("Demonstrated research / publication background significantly bolsters MEXT, GKS, and research-focused master's.")
        if has_english_proof:
            strengths.append(f"Documented language capability ({profile.english_test}) eliminates initial application disqualification risks.")
        else:
            cautions.append("No English test score recorded yet: schedule IELTS/TOEFL early or verify medium-of-instruction waivers.")

        if not work_eligible_for_pro:
            cautions.append("Under 2 years experience excludes awards requiring 2+ years post-grad employment (Chevening, DAAD EPOS). Focus on Erasmus Mundus, GKS, MEXT, and university waivers.")

        return {
            "applicant_name": profile.full_name or "Applicant",
            "nationality": profile.nationality,
            "normalized_gpa": normalized_gpa,
            "academic_standing": academic_standing,
            "academic_tier": academic_tier,
            "work_years": work_years,
            "work_status": work_status,
            "work_eligible_for_pro": work_eligible_for_pro,
            "has_english_proof": has_english_proof,
            "language_summary": lang_str,
            "target_field": profile.target_degree_field,
            "target_countries": profile.target_countries or ["Global / Any"],
            "strengths": strengths,
            "cautions": cautions,
            "recommended_focus": "Multi-track strategy: 2 High-Prestige Full Scholarships + 2 High-Acceptance Government Scholarships + 2 University Fee Waivers.",
            "search_keywords": search_keywords
        }

profile_agent = ProfileAgent()
