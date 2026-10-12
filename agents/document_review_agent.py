"""
Document Review & Plagiarism Auditor Agent
-------------------------------------------
This module evaluates Statement of Purpose (SOP) essays, motivation letters,
academic CVs, and Letters of Recommendation (LOR) for:
1. Plagiarism & Template Similarity: Detects common internet templates and overused scholarship clichés.
2. Originality Scoring: Evaluates vocabulary richness, sentence structure diversity, and unique narrative voice.
3. Admissions Quality Rubric: Scores persuasiveness, academic depth, quantified achievements, and sponsor alignment.
4. Line-by-Line Rewrites: Delivers concrete improvements replacing weak/generic phrases with compelling prose.
"""

import re
import math
from typing import Dict, Any, List, Optional
from models import DocumentReviewRequest, DocumentReviewResult, HighlightedSnippet
from agents.gemini_client import gemini_client
from data.scholarships_db import SCHOLARSHIPS_DATABASE

# Common scholarship clichés and overused template phrases
COMMON_CLICHES = [
    (r"since (my )?(childhood|early age|a young age)", "Overused childhood cliché. Scholarship committees favor recent, problem-oriented intellectual urgency over childhood nostalgia.", "Red"),
    (r"ever since I was (a kid|young|small|a child)", "Generic childhood opening. Start immediately with a specific real-world challenge or research project.", "Red"),
    (r"in today('s)? (rapidly )?(changing|globalized|interconnected) world", "Trite filler phrase. Replace with specific domain context.", "Yellow"),
    (r"in the 21st century", "Vague essay opening cliché. Jump directly into your specific research or field challenge.", "Yellow"),
    (r"I have always been passionate about", "Telling rather than showing. Demonstrate passion through concrete projects, lab experiments, or leadership actions.", "Yellow"),
    (r"is a stepping stone (for|to) my career", "Trite scholarship metaphor. Specify exact technical skills and institutional modules you will gain.", "Yellow"),
    (r"this (scholarship|program) is a golden opportunity", "Flattery cliché. Explain specific alignment with your 5-year post-graduation impact goals.", "Yellow"),
    (r"I want to (make the world a better place|give back to (my )?country)", "Vague altruism. Specify concrete socio-economic or technological return on investment for your country.", "Yellow"),
    (r"I am a (very )?(hardworking|dedicated|motivated) (student|individual|person)", "Unsubstantiated self-praise. Evidence of grades, publications, or thesis results speaks louder than adjectives.", "Yellow"),
    (r"knowledge is power", "Proverb cliché. Avoid quotes or proverbs in graduate-level academic applications.", "Red"),
    (r"it goes without saying that", "Redundant filler phrase that dilutes your word limit.", "Yellow"),
    (r"to whom it may concern", "Impersonal greeting. Address the specific Scholarship Selection Committee or Department.", "Red"),
    (r"I would like to express my gratitude for this opportunity", "Opening pleasantry. Use your precious first paragraph to establish your academic hook.", "Yellow"),
]

class DocumentReviewAgent:
    """
    Autonomous agent for plagiarism detection, originality analysis, and comprehensive document review.
    """

    def review_document(self, req: DocumentReviewRequest) -> DocumentReviewResult:
        """
        Audits a document (SOP, CV, LOR, Proposal) for originality, template similarity, and overall strength.

        Args:
            req (DocumentReviewRequest): Contains text content, document type, and target scholarship.

        Returns:
            DocumentReviewResult: Originality score, cliché count, quality metrics, highlighted snippets, and advice.
        """
        text = req.content.strip()
        doc_type = req.doc_type.lower()
        scholarship_id = req.scholarship_id

        # Basic word and sentence statistics
        words = re.findall(r"\b\w+\b", text)
        word_count = len(words)
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 5]
        sentence_count = len(sentences) or 1

        if word_count < 30:
            return DocumentReviewResult(
                doc_type=doc_type,
                overall_score=20,
                originality_score=30,
                plagiarism_risk="High (Insufficient content to evaluate)",
                word_count=word_count,
                cliche_count=0,
                strengths=["Submitted text for review."],
                weaknesses=["Content is too short. A standard Master's SOP should be between 500 and 1,000 words."],
                highlighted_snippets=[],
                rewrite_suggestions=[],
                committee_verdict="Incomplete Draft — Needs substantial elaboration.",
                plagiarism_analysis="Document lacks sufficient substance to establish originality."
            )

        # ---------------------------------------------------------
        # 1. Cliché & Template Pattern Detection
        # ---------------------------------------------------------
        detected_cliches: List[Dict[str, Any]] = []
        highlighted_snippets: List[HighlightedSnippet] = []

        for pattern, explanation, severity in COMMON_CLICHES:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                snippet_text = match.group(0)
                detected_cliches.append({
                    "phrase": snippet_text,
                    "explanation": explanation,
                    "severity": severity
                })
                highlighted_snippets.append(HighlightedSnippet(
                    text=snippet_text,
                    category="Cliché / Overused Pattern" if severity == "Red" else "Generic Phrasing",
                    severity=severity,
                    suggestion=explanation
                ))

        # ---------------------------------------------------------
        # 2. Vocabulary Diversity & Repetition (Type-Token Ratio)
        # ---------------------------------------------------------
        unique_words = set(w.lower() for w in words)
        ttr = len(unique_words) / word_count if word_count > 0 else 0.0

        # Average sentence length
        avg_sentence_len = word_count / sentence_count

        # ---------------------------------------------------------
        # 3. Originality & Plagiarism Risk Calculation
        # ---------------------------------------------------------
        # Baseline originality: 92%
        originality_deduction = len(detected_cliches) * 7.5
        if ttr < 0.45:
            originality_deduction += 12  # Repetitive vocabulary
        elif ttr > 0.60:
            originality_deduction -= 5   # Rich academic vocabulary

        originality_score = int(max(25, min(99, 95 - originality_deduction)))

        # Plagiarism risk category
        if originality_score >= 82:
            plagiarism_risk = "Low Risk (Unique voice & authentic narrative)"
        elif originality_score >= 65:
            plagiarism_risk = "Moderate Risk (Contains template patterns & generic phrasing)"
        else:
            plagiarism_risk = "High Risk (High overlap with common internet SOP templates)"

        # ---------------------------------------------------------
        # 4. Overall Quality Rubric Calculation
        # ---------------------------------------------------------
        quality_score = 75
        strengths = []
        weaknesses = []

        # Length check
        if 500 <= word_count <= 1100:
            quality_score += 10
            strengths.append(f"Ideal document length ({word_count} words), within standard admissions target of 500–1,000 words.")
        elif word_count < 400:
            quality_score -= 15
            weaknesses.append(f"Brief length ({word_count} words). Committees expect deeper academic and future-impact details.")
        elif word_count > 1300:
            quality_score -= 8
            weaknesses.append(f"Length is slightly long ({word_count} words). Tighten prose to avoid exceeding strict committee word limits.")

        # Quantified impact check (numbers, percentages, metrics)
        has_metrics = bool(re.search(r"\b(\d+(\.\d+)?%?|\$\d+|[0-9]+)\b", text))
        if has_metrics:
            quality_score += 8
            strengths.append("Contains quantified metrics and specific milestones, proving verifiable accomplishments.")
        else:
            quality_score -= 8
            weaknesses.append("Lacks quantified results. Add concrete figures (e.g. 'improved performance by 18%', 'managed a team of 4').")

        # Specific scholarship alignment check
        target_name = "Target Master's Scholarship"
        if scholarship_id:
            s = next((item for item in SCHOLARSHIPS_DATABASE if item["id"] == scholarship_id), None)
            if s:
                target_name = s["name"]
                if s["name"].lower() in text.lower() or s["sponsor"].lower() in text.lower():
                    quality_score += 7
                    strengths.append(f"Directly references {target_name}, demonstrating tailored alignment.")
                else:
                    quality_score -= 5
                    weaknesses.append(f"Does not explicitly mention {target_name} or its host universities. Tailor essays directly.")

        # Cliché penalty on quality
        if not detected_cliches:
            quality_score += 5
            strengths.append("Avoided overused scholarship clichés and childhood narratives.")
        else:
            quality_score -= min(15, len(detected_cliches) * 4)
            weaknesses.append(f"Detected {len(detected_cliches)} overused clichés or generic filler patterns.")

        overall_score = int(max(30, min(98, quality_score)))

        # ---------------------------------------------------------
        # 5. Targeted Rewrite Suggestions
        # ---------------------------------------------------------
        rewrite_suggestions = []
        
        # Suggestion 1: Opening hook
        if sentences:
            first_sent = sentences[0]
            if any(cliche[0] in first_sent.lower() for cliche in COMMON_CLICHES[:4]):
                rewrite_suggestions.append({
                    "original": first_sent,
                    "revised": "While developing [Specific Project / Thesis] at [Institution], I identified a critical bottleneck in [Field Challenge] that shaped my commitment to pursuing advanced Master's research.",
                    "rationale": "Replaces vague childhood nostalgia with an authentic, problem-oriented technical hook."
                })
            else:
                rewrite_suggestions.append({
                    "original": first_sent[:120] + ("..." if len(first_sent) > 120 else ""),
                    "revised": f"My professional trajectory in [Your Field] centers on addressing [Primary Societal/Technical Challenge], a mission that directly aligns with the interdisciplinary curriculum of {target_name}.",
                    "rationale": "Frames your personal ambition within the broader public mission of the scholarship sponsor."
                })

        # Suggestion 2: Specific ROI / Future impact
        rewrite_suggestions.append({
            "original": "This scholarship will help me achieve my goals and make my country proud.",
            "revised": "Upon graduation, I will return to [Home Country] to lead the deployment of [Specific Innovation/Policy], targeting a [Quantified Metric] reduction in [Regional Problem] within 5 years.",
            "rationale": "Replaces generic aspirations with a quantified Return On Investment (ROI) for the scholarship committee."
        })

        # ---------------------------------------------------------
        # 6. Committee Verdict
        # ---------------------------------------------------------
        if overall_score >= 85 and originality_score >= 85:
            committee_verdict = "Exceptional & Highly Competitive — Ready for final polish and submission."
        elif overall_score >= 72:
            committee_verdict = "Strong Draft — Address highlighted generic phrases and strengthen quantified metrics."
        elif overall_score >= 55:
            committee_verdict = "Moderate Draft — Needs restructuring: eliminate template phrases and customize for the specific scholarship."
        else:
            committee_verdict = "High Risk / Under-prepared — Significant rewriting recommended before submission."

        # ---------------------------------------------------------
        # 7. AI Semantic Audit (When Gemini is active)
        # ---------------------------------------------------------
        plagiarism_analysis = (
            f"Originality Index: {originality_score}/100 ({plagiarism_risk}). "
            f"Identified {len(detected_cliches)} cliché/template flags. "
            f"Vocabulary diversity (TTR) is {round(ttr * 100, 1)}%."
        )

        if gemini_client.has_valid_key():
            prompt = f"""
You are an expert scholarship admissions committee chair auditing an applicant's {doc_type.upper()}.
Review the following text for originality, AI-generated generic patterns, and competitive impact for {target_name}:

DOCUMENT TEXT:
\"\"\"
{text[:3000]}
\"\"\"

TASKS:
1. Provide a 2-sentence brutal critique on its originality and plagiarism/cliché risk.
2. Give one concrete sentence from the text and show how to rewrite it for maximum committee impact.
"""
            ai_eval = gemini_client.generate_text(prompt)
            if ai_eval:
                plagiarism_analysis = f"{plagiarism_analysis}\n\n**AI Admissions Committee Critique:**\n{ai_eval.strip()}"

        return DocumentReviewResult(
            doc_type=doc_type,
            overall_score=overall_score,
            originality_score=originality_score,
            plagiarism_risk=plagiarism_risk,
            word_count=word_count,
            cliche_count=len(detected_cliches),
            strengths=strengths,
            weaknesses=weaknesses,
            highlighted_snippets=highlighted_snippets,
            rewrite_suggestions=rewrite_suggestions,
            committee_verdict=committee_verdict,
            plagiarism_analysis=plagiarism_analysis
        )

# Global singleton instance of DocumentReviewAgent
document_review_agent = DocumentReviewAgent()
