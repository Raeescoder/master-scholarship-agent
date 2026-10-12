"""
Roadmap & Application Strategy Agent
------------------------------------
This module designs an actionable master's scholarship application strategy:
1. Four-phase milestone timeline leading up to the official submission deadlines.
2. Statement of Purpose (SOP) narrative blueprint (The Hook, Academic Bridge, Program Fit, ROI/Impact).
3. Comprehensive document preparation matrix with critical alerts.
4. Referee selection tactics (Recommendation letters) and interview defense tips.
"""

from typing import Dict, Any, List
from models import UserProfile, ApplicationRoadmap
from data.scholarships_db import SCHOLARSHIPS_DATABASE
from agents.gemini_client import gemini_client

class RoadmapAgent:
    """
    Autonomous strategic planning agent:
    - Synthesizes student aspirations into a chronological 4-phase preparation plan.
    - Blueprints high-impact motivation letter structures.
    - Prepares candidate for letters of recommendation and selection interviews.
    """

    def generate_roadmap(self, profile: UserProfile, scholarship_id: str) -> ApplicationRoadmap:
        """
        Generates a comprehensive application roadmap for a chosen scholarship.

        Args:
            profile (UserProfile): Candidate's academic profile and preferences.
            scholarship_id (str): Unique scholarship key.

        Returns:
            ApplicationRoadmap: Structured timeline, SOP guidelines, document matrix, and interview advice.
        """
        # Retrieve scholarship metadata
        scholarship = next((s for s in SCHOLARSHIPS_DATABASE if s["id"] == scholarship_id), None)
        s_name = scholarship["name"] if scholarship else scholarship_id.replace("_", " ").title()
        typical_deadline = scholarship.get("typical_deadline", "December - February") if scholarship else "Rolling / Annual"

        # ---------------------------------------------------------
        # 1. Four-Phase Milestone Timeline
        # ---------------------------------------------------------
        timeline_steps = [
            {
                "phase": "Phase 1: Foundation & Eligibility Lock-in",
                "timing": "4 - 6 Months Before Deadline",
                "tasks": [
                    "Order official undergraduate academic transcripts and degree certificates with certified English translations.",
                    f"Confirm language test booking (IELTS/TOEFL) to achieve required cutoff ({scholarship.get('language_requirement', 'IELTS 6.5+') if scholarship else 'IELTS 6.5'}).",
                    "Identify 2-3 academic professors or workplace supervisors for Recommendation Letters."
                ]
            },
            {
                "phase": "Phase 2: Narrative & Proposal Engineering",
                "timing": "2 - 3 Months Before Deadline",
                "tasks": [
                    f"Draft the Statement of Purpose (SOP) focused on why {s_name} is essential for your career in {profile.target_degree_field}.",
                    "Prepare an updated 2-page Academic CV (using Harvard or Europass style, avoiding non-standard visual graphics).",
                    "If research-focused (MEXT/ETH/GKS): Draft a 1,000-word Study Plan / Preliminary Research Proposal."
                ]
            },
            {
                "phase": "Phase 3: Referee Package & Document Finalization",
                "timing": "4 - 6 Weeks Before Deadline",
                "tasks": [
                    "Provide your referees with a 'Brag Sheet' detailing your achievements and bullet points on why you need this award.",
                    "Obtain signed & stamped Letters of Recommendation on official university/company letterhead.",
                    "Review all documents against the official scholarship upload guidelines (file sizes, PDF formats)."
                ]
            },
            {
                "phase": "Phase 4: Portal Submission & Verification",
                "timing": "1 - 2 Weeks Before Deadline",
                "tasks": [
                    "Submit application portal forms at least 7 days ahead of deadline to avoid server crashes.",
                    "Double check referee submission status on the portal.",
                    "Download confirmation receipt and save application reference number."
                ]
            }
        ]

        # ---------------------------------------------------------
        # 2. Statement of Purpose (SOP) Narrative Blueprint
        # ---------------------------------------------------------
        sop_framework = {
            "hook_section": f"Open with a compelling problem-oriented moment: Explain the exact real-world challenge in {profile.target_degree_field} that inspired your journey in {profile.nationality}.",
            "academic_bridge": f"Bridge your undergraduate background ({profile.bachelor_field}, GPA {profile.gpa}) with the target Master's: highlight capstone projects, lab work, or relevant technical coursework.",
            "program_alignment": f"Explain why {s_name} specifically: cite 2 professors, labs, or unique consortium modules that are unavailable in your home country.",
            "impact_and_future_vision": "Address the scholarship sponsor's mission: outline your 5-year post-graduation plan and how you will drive technological, economic, or policy advancements."
        }

        # ---------------------------------------------------------
        # 3. Document Preparation Matrix
        # ---------------------------------------------------------
        required_documents = [
            {
                "document": "Official Transcripts & Degree Certificate",
                "status": "Mandatory",
                "tip": "Ensure grading scale explanation is included on reverse side or accompanying registrar letter."
            },
            {
                "document": "Statement of Purpose / Motivation Letter",
                "status": "Critical",
                "tip": "Limit to 1.5 - 2 pages (800-1000 words). Never use generic templates."
            },
            {
                "document": "Letters of Recommendation (2-3)",
                "status": "Mandatory",
                "tip": "At least one academic professor who taught relevant technical courses and can attest to your intellectual grit."
            },
            {
                "document": "Language Proficiency Proof",
                "status": "Mandatory",
                "tip": f"Currently noted: {profile.english_test or 'Required - book test immediately'}."
            },
            {
                "document": "Standard Academic CV / Resume",
                "status": "Mandatory",
                "tip": "Highlight publications, hackathons, awards, and quantified leadership results."
            }
        ]

        # ---------------------------------------------------------
        # 4. Referee Selection & Interview Protocol
        # ---------------------------------------------------------
        recommendation_tips = [
            "Select professors who know your work deeply rather than high-title administrators who only know your name.",
            "Send them your SOP draft, CV, and bullet points of projects you did in their class 3-4 weeks in advance.",
            "Ask referees to emphasize your resilience, academic curiosity, and collaborative mindset."
        ]

        interview_prep = [
            "Master the 2-minute elevator pitch: Who you are, what problems you solve, and why this scholarship.",
            "Use the STAR method (Situation, Task, Action, Result) for behavioral questions on overcoming obstacles.",
            "Be prepared to answer: 'Why should the committee invest public funds in you over hundreds of other applicants?'"
        ]

        # If Gemini is active, generate custom narrative hook
        if gemini_client.has_valid_key():
            prompt = f"""
Act as a world-class scholarship admissions strategist.
Create a hyper-personalized Statement of Purpose hook and unique angle for:
- Student: from {profile.nationality}
- Desired Master's: {profile.target_degree_field}
- Background: {profile.bachelor_field}
- Scholarship: {s_name}

Provide:
1. One powerful opening hook sentence.
2. Two specific research/academic angles to tie into the motivation letter.
"""
            ai_tips = gemini_client.generate_text(prompt)
            if ai_tips:
                sop_framework["ai_custom_angle"] = ai_tips.strip()

        return ApplicationRoadmap(
            scholarship_id=scholarship_id,
            scholarship_name=s_name,
            estimated_deadline=typical_deadline,
            timeline_steps=timeline_steps,
            sop_framework=sop_framework,
            required_documents=required_documents,
            recommendation_tips=recommendation_tips,
            interview_prep=interview_prep
        )

# Global singleton instance of RoadmapAgent
roadmap_agent = RoadmapAgent()
