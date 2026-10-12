"""
Live Scholarship Discovery Agent
--------------------------------
This module discovers relevant Master's scholarships tailored to the applicant's profile.
It performs two complementary actions:
1. Multi-factor semantic scoring against a curated international repository of 16+ flagship scholarships.
2. Real-time Google Search Grounding using Google Gemini API (when configured) to discover upcoming
   intake deadlines, country quotas, and consortium calls for the 2025/2026/2027 academic years.
"""

import json
import re
from typing import List, Dict, Any
from models import UserProfile
from data.scholarships_db import SCHOLARSHIPS_DATABASE
from agents.gemini_client import gemini_client

class DiscoveryAgent:
    """
    Autonomous agent responsible for discovering and ranking scholarship opportunities:
    - Filters by host countries, target fields, GPA minimums, and work requirements.
    - Connects with Gemini Google Search tool to ground recommendations in real-time deadlines.
    - Yields ranked match candidates and strategic advisory insights.
    """

    def discover_scholarships(self, profile: UserProfile, profile_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes scholarship discovery and match suitability calculation.

        Args:
            profile (UserProfile): The student's academic and biographical profile.
            profile_summary (Dict[str, Any]): Synthesized evaluation metrics from ProfileAgent.

        Returns:
            Dict[str, Any]: {
                "matched_scholarships": List of scored scholarship objects,
                "ai_insights": Strategic recommendations (grounded via web search or expert heuristics),
                "search_grounded": True if live Google Search was triggered.
            }
        """
        normalized_gpa = profile_summary["normalized_gpa"]
        work_years = profile.work_experience_years
        target_countries = [c.lower() for c in profile.target_countries]
        target_field = profile.target_degree_field.lower()

        matched_scholarships = []
        
        # ---------------------------------------------------------
        # 1. Multi-Dimensional Ranking against Knowledge Base
        # ---------------------------------------------------------
        for item in SCHOLARSHIPS_DATABASE:
            score = 70  # Baseline score for general eligibility

            # Field Alignment (+15 points if subject aligns with scholarship target domains)
            fields_lower = [f.lower() for f in item["target_fields"]]
            if "all fields" in fields_lower or any(word in target_field for f in fields_lower for word in f.split()):
                score += 15

            # Geographic Destination Alignment (+10 points if host country matches user goals)
            hosts_lower = " ".join([h.lower() for h in item["host_countries"]])
            if not target_countries or any(tc in hosts_lower for tc in target_countries) or "global" in target_countries:
                score += 10
            elif target_countries:
                score -= 10  # Mild penalty if user has specific country preferences that differ

            # Work Experience Filter Check
            # Awards requiring 2+ years strictly penalize candidates lacking sufficient employment
            if "2 years" in item["work_exp_requirement"].lower() or "3,000 hours" in item["work_exp_requirement"].lower():
                if work_years < 2.0:
                    score -= 25  # Substantial penalty for failing mandatory experience quota
                else:
                    score += 10

            # Academic GPA Filter Check
            if normalized_gpa < 3.0 and ("3.5" in item["min_gpa_requirement"] or "top 10%" in item["min_gpa_requirement"].lower()):
                score -= 20
            elif normalized_gpa >= 3.6:
                score += 10

            # Clamp score between 20% and 98%
            score = max(20, min(98, score))
            
            item_copy = dict(item)
            item_copy["computed_suitability"] = score
            matched_scholarships.append(item_copy)

        # Sort scholarships descending by computed match score
        matched_scholarships.sort(key=lambda x: x["computed_suitability"], reverse=True)

        # ---------------------------------------------------------
        # 2. Live Google Search Grounding with Gemini
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # 3. Intelligent Heuristic Fallback
        # ---------------------------------------------------------
        if not ai_insights:
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

# Global singleton instance of DiscoveryAgent
discovery_agent = DiscoveryAgent()
