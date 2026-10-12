import json
import re
from typing import List, Dict, Any
from models import UserProfile
from data.scholarships_db import SCHOLARSHIPS_DATABASE
from agents.gemini_client import gemini_client

class DiscoveryAgent:
    """
    Finds scholarships matching user profile using our curated international repository,
    supplemented by live Google Search Grounding with Gemini when an API key is available.
    """

    def discover_scholarships(self, profile: UserProfile, profile_summary: Dict[str, Any]) -> Dict[str, Any]:
        normalized_gpa = profile_summary["normalized_gpa"]
        work_years = profile.work_experience_years
        target_countries = [c.lower() for c in profile.target_countries]
        target_field = profile.target_degree_field.lower()

        matched_scholarships = []
        
        # Filter and rank from curated repository
        for item in SCHOLARSHIPS_DATABASE:
            score = 70 # baseline eligibility
            
            # Field relevance
            fields_lower = [f.lower() for f in item["target_fields"]]
            if "all fields" in fields_lower or any(word in target_field for f in fields_lower for word in f.split()):
                score += 15

            # Country relevance
            hosts_lower = " ".join([h.lower() for h in item["host_countries"]])
            if not target_countries or any(tc in hosts_lower for tc in target_countries) or "global" in target_countries:
                score += 10
            elif target_countries:
                # If specific country was requested and doesn't match host, reduce score slightly
                score -= 10

            # Work experience filter
            if "2 years" in item["work_exp_requirement"].lower() or "3,000 hours" in item["work_exp_requirement"].lower():
                if work_years < 2.0:
                    score -= 25 # Penalty for lacking mandatory work years
                else:
                    score += 10

            # GPA filter
            if normalized_gpa < 3.0 and ("3.5" in item["min_gpa_requirement"] or "top 10%" in item["min_gpa_requirement"].lower()):
                score -= 20
            elif normalized_gpa >= 3.6:
                score += 10

            # Clamping score
            score = max(20, min(98, score))
            
            item_copy = dict(item)
            item_copy["computed_suitability"] = score
            matched_scholarships.append(item_copy)

        # Sort by suitability
        matched_scholarships.sort(key=lambda x: x["computed_suitability"], reverse=True)

        # Now check if Gemini live search is available to augment with live search insights
        ai_insights = ""
        search_grounded = False

        if gemini_client.has_valid_key():
            prompt = f"""
You are an expert AI scholarship researcher.
A Master's degree applicant has the following profile:
- Citizenship: {profile.nationality}
- Desired Master's Field: {profile.target_degree_field}
- Undergraduate Field: {profile.bachelor_field}
- Normalized GPA: {normalized_gpa} / 4.0
- Work Experience: {work_years} years
- Target Countries: {', '.join(profile.target_countries) if profile.target_countries else 'Any / Flexible'}
- English Proficiency: {profile.english_test or 'None specified'}
- Funding Preference: {profile.funding_type_needed}

TASK:
1. Search Google for up-to-date Master's scholarship deadlines for the 2025/2026/2027 academic intakes relevant to students from {profile.nationality} pursuing {profile.target_degree_field}.
2. Provide 3 specific and highly actionable recommendations, mentioning exact program names (e.g., specific Erasmus Mundus consortium titles in this field, bilateral government awards, or top university tuition waivers).
3. Warn about any strict eligibility traps (e.g. post-study return requirements, work experience verification, or early application cutoffs).

Keep your response structured, concise, and focused on maximizing their chances.
"""
            ai_text = gemini_client.generate_with_search(prompt)
            if ai_text:
                ai_insights = ai_text
                search_grounded = True

        if not ai_insights:
            # Fallback high-quality curated strategic insight
            ai_insights = (
                f"### Strategic Advisor Insight for {profile.nationality} Applicants in {profile.target_degree_field}\n\n"
                f"- **Top Priority 1 (Europe - Erasmus Mundus)**: Apply to 2 to 3 Erasmus Mundus Joint Master Degrees (EMJM) matching {profile.target_degree_field}. EMJM allows up to 3 applications simultaneously with no application fee for most consortiums.\n"
                f"- **Top Priority 2 (Government Sponsorships)**: If you possess 2+ years of verified professional experience, prioritize Chevening (UK) or DAAD EPOS (Germany). If under 2 years, focus on Turkiye Burslari, MEXT (Japan), or GKS (Korea) which accept recent graduates.\n"
                f"- **Academic Match**: With a normalized GPA of {normalized_gpa}/4.0, your academic profile is in the **{profile_summary['academic_tier']}** category. Complement fully-funded government programs with university-level tuition waivers."
            )

        return {
            "matched_scholarships": matched_scholarships,
            "ai_insights": ai_insights,
            "search_grounded": search_grounded
        }

discovery_agent = DiscoveryAgent()
