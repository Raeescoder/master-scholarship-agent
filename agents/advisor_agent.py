from typing import List, Optional
from models import UserProfile, ChatMessage
from agents.gemini_client import gemini_client
from data.scholarships_db import SCHOLARSHIPS_DATABASE

class AdvisorAgent:
    """
    Interactive scholarship advisor providing contextual guidance, SOP critiques,
    eligibility queries, and interview coaching.
    """

    def reply(self, messages: List[ChatMessage], profile: Optional[UserProfile] = None, scholarship_id: Optional[str] = None) -> str:
        # Build context
        context_parts = []
        if profile:
            context_parts.append(
                f"Applicant Profile: Name: {profile.full_name}, Nationality: {profile.nationality}, "
                f"Target Master's Field: {profile.target_degree_field}, Undergrad Field: {profile.bachelor_field}, "
                f"GPA: {profile.gpa}/{profile.gpa_scale}, Work Exp: {profile.work_experience_years} years, "
                f"Language: {profile.english_test or 'None'}, Target Countries: {', '.join(profile.target_countries) if profile.target_countries else 'Any'}."
            )

        if scholarship_id:
            s = next((item for item in SCHOLARSHIPS_DATABASE if item["id"] == scholarship_id), None)
            if s:
                context_parts.append(
                    f"Selected Scholarship Context: {s['name']} (Sponsor: {s['sponsor']}, Hosts: {', '.join(s['host_countries'])}, "
                    f"Coverage: {s['coverage_details']}, GPA Req: {s['min_gpa_requirement']}, Exp Req: {s['work_exp_requirement']})."
                )

        system_instruction = (
            "You are an elite International Master's Scholarship Admissions Advisor. "
            "You have helped hundreds of students win full government & university scholarships like Erasmus Mundus, "
            "Chevening, DAAD, Fulbright, MEXT, GKS, and Swedish Institute.\n\n"
            "Your advice is pragmatic, actionable, encouraging, and razor-sharp. "
            "Always tailor answers directly to the applicant's specific profile context provided. "
            "Highlight practical strategies: how to offset lower GPAs, how to frame leadership, how to choose referees, and how to structure motivation letters."
        )

        # If Gemini is active
        if gemini_client.has_valid_key():
            prompt = "\n\n".join(context_parts) + "\n\nConversation:\n"
            for m in messages:
                prompt += f"{m.role.upper()}: {m.content}\n"
            prompt += "ASSISTANT: "

            reply_text = gemini_client.generate_text(prompt, system_instruction=system_instruction)
            if reply_text:
                return reply_text.strip()

        # Fallback intelligent response generator
        last_msg = messages[-1].content.lower() if messages else ""
        
        if "sop" in last_msg or "motivation" in last_msg or "statement of purpose" in last_msg:
            return (
                "**Essential Rules for a Winning Master's Scholarship SOP:**\n\n"
                "1. **Never start with a childhood cliché** (e.g. 'Since I was a child I loved technology'). Begin with a concrete moment of intellectual urgency or an unsolved problem in your home country.\n"
                "2. **The 30/40/30 Rule**:\n"
                "   - *First 30%*: Who you are, your foundational training, and the driving question behind your Master's ambition.\n"
                "   - *Middle 40%*: Why this exact scholarship & university? Mention specific research modules, professors, or lab initiatives.\n"
                "   - *Final 30%*: The 'Return on Investment' for the scholarship committee. Exactly what job and societal impact will you execute upon graduating?\n"
                "3. **Show, Don't Tell**: Don't say 'I am a passionate leader'. State: 'As lead engineer for X project, I organized a 5-member team to deliver Y under Z constraint.'\n\n"
                "*(Tip: Set your Gemini API key in the top bar to have me review your custom SOP paragraphs in real time!)*"
            )
        elif "gpa" in last_msg or "low grade" in last_msg or "cgpa" in last_msg:
            return (
                "**How to Overcome a Lower GPA for Master's Scholarships:**\n\n"
                "- **Apply to Holistic Evaluators**: Programs like Erasmus Mundus, Turkiye Burslari, and DAAD evaluate the full candidate dossier. A 3.0 with strong project experience often defeats a 3.8 with zero initiative.\n"
                "- **Highlight an Upward Trajectory**: If your final two years had stronger grades than your freshman year, explain that your passion crystallized as you reached advanced coursework.\n"
                "- **Showcase Real Proof of Competence**: Relevant work experience, Github repositories, research publications, or certifications directly neutralize grade doubts.\n"
                "- **Recommenders' Backing**: Request a professor to specifically state: *'Their exam score understates their exceptional analytical capability in laboratory problem solving.'*"
            )
        elif "recommendation" in last_msg or "reference" in last_msg or "referee" in last_msg:
            return (
                "**Recommendation Letter (LOR) Strategy:**\n\n"
                "- **Who to ask**: Choose professors who know you personally (e.g., your thesis advisor or project mentor) over famous department deans who barely know your face.\n"
                "- **Prepare a 'Brag Packet'**: Send your referees your CV, your SOP draft, and bullet points reminding them of the specific presentations, projects, and grades you achieved in their class.\n"
                "- **Key Qualities to Validate**: Ask one referee to highlight your academic rigor and intellectual curiosity, and another to highlight your teamwork, reliability, and leadership."
            )
        else:
            name = profile.full_name if profile else "applicant"
            field = profile.target_degree_field if profile else "your target degree"
            return (
                f"Hello {name}! As your Master's Scholarship Advisor, I am here to help you secure full funding for {field}.\n\n"
                "Here are key strategic areas I can assist you with:\n"
                "1. **Eligibility Check**: Clarifying GPA conversion, nationality quotas, and work experience criteria.\n"
                "2. **SOP & Motivation Letter**: Structuring your essay, crafting opening hooks, and highlighting societal impact.\n"
                "3. **Scholarship Selection**: Balancing reach scholarships (e.g. Gates, ETH ESOP) with high-intake opportunities (Erasmus Mundus, Turkiye Burslari, DAAD).\n"
                "4. **Supervisor Outreach**: How to contact professors for scholarships requiring university acceptance (like MEXT or Swiss Excellence).\n\n"
                "What specific question or scholarship would you like to explore?"
            )

advisor_agent = AdvisorAgent()
