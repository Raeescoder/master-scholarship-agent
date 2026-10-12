from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    full_name: Optional[str] = "Applicant"
    nationality: str = Field(..., description="Country of citizenship")
    residence_country: Optional[str] = None
    bachelor_field: str = Field(..., description="Undergraduate major / degree")
    gpa: float = Field(..., description="Grade Point Average")
    gpa_scale: float = Field(default=4.0, description="GPA scale, e.g. 4.0, 5.0, 10.0, or 100")
    target_degree_field: str = Field(..., description="Intended Master's subject / specialization")
    target_countries: List[str] = Field(default_factory=list, description="Desired destination countries or regions")
    funding_type_needed: str = Field(default="Fully Funded", description="'Fully Funded', 'Partial Waiver', or 'Any'")
    english_test: Optional[str] = Field(default=None, description="e.g. IELTS 7.5, TOEFL 100, Duolingo 125, or Pending")
    gre_score: Optional[str] = Field(default=None, description="GRE / GMAT score or 'None'")
    work_experience_years: float = Field(default=0.0, description="Years of professional or relevant work experience")
    research_experience: Optional[str] = Field(default=None, description="Publications, thesis, lab work")
    financial_need_level: str = Field(default="High", description="High, Medium, or Any")
    additional_notes: Optional[str] = Field(default="", description="Any special circumstances or preferences")

class Scholarship(BaseModel):
    id: str
    name: str
    sponsor: str
    host_countries: List[str]
    target_fields: List[str]
    funding_type: str
    coverage_details: str
    degree_level: str = "Master's"
    typical_deadline: str
    eligible_nationalities: str = "All Nationalities"
    min_gpa_requirement: str = "Flexible / Holistically Reviewed"
    language_requirement: str = "IELTS 6.5+ or TOEFL 85+ or English taught degree"
    work_exp_requirement: str = "None required"
    description: str
    official_url: str
    tags: List[str] = Field(default_factory=list)

class MatchEvaluation(BaseModel):
    scholarship_id: str
    scholarship_name: str
    match_score: int = Field(..., ge=0, le=100)
    verdict: str
    strengths: List[str]
    potential_obstacles: List[str]
    checklist: Dict[str, bool] = Field(default_factory=dict)
    key_advice: str

class DiscoveryResponse(BaseModel):
    profile_summary: Dict[str, Any]
    matched_scholarships: List[Dict[str, Any]]
    ai_insights: str
    search_grounded: bool = False

class RoadmapRequest(BaseModel):
    profile: UserProfile
    scholarship_id: str

class ApplicationRoadmap(BaseModel):
    scholarship_id: str
    scholarship_name: str
    estimated_deadline: str
    timeline_steps: List[Dict[str, Any]]
    sop_framework: Dict[str, Any]
    required_documents: List[Dict[str, Any]]
    recommendation_tips: List[str]
    interview_prep: List[str]

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    profile: Optional[UserProfile] = None
    messages: List[ChatMessage]
    selected_scholarship_id: Optional[str] = None

class ApiKeyRequest(BaseModel):
    api_key: str

class ApiKeyStatus(BaseModel):
    has_key: bool
    source: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    nationality: str

class LoginRequest(BaseModel):
    email: str
    password: str

class BookmarkRequest(BaseModel):
    scholarship_id: str
