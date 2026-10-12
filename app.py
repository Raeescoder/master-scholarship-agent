from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import config, BASE_DIR
from db import UserService
from models import (
    UserProfile,
    RoadmapRequest,
    ChatRequest,
    ApiKeyRequest,
    ApiKeyStatus,
    DiscoveryResponse,
    RegisterRequest,
    LoginRequest,
    BookmarkRequest
)
from data.scholarships_db import SCHOLARSHIPS_DATABASE
from agents.profile_agent import profile_agent
from agents.discovery_agent import discovery_agent
from agents.eligibility_agent import eligibility_agent
from agents.roadmap_agent import roadmap_agent
from agents.advisor_agent import advisor_agent
from agents.gemini_client import gemini_client

app = FastAPI(
    title="ScholarAI - Global Master's Scholarship Finder Agent",
    description="Agentic system for international master's scholarship discovery, eligibility analysis, and application strategy.",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files setup
static_path = BASE_DIR / "static"
if not static_path.exists():
    static_path.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Authentication Dependencies
def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "").strip()
    return UserService.get_user_by_token(token)

def require_user(authorization: Optional[str] = Header(None)) -> dict:
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required. Please sign in.")
    return user

# Authentication Endpoints
@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    try:
        user_data = UserService.register_user(
            email=req.email,
            password=req.password,
            full_name=req.full_name,
            nationality=req.nationality
        )
        return {"success": True, "user": user_data, "token": user_data["token"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    try:
        user_data = UserService.login_user(
            email=req.email,
            password=req.password
        )
        return {"success": True, "user": user_data, "token": user_data["token"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        UserService.logout(token)
    return {"success": True, "message": "Logged out successfully."}

@app.get("/api/auth/me")
async def get_me(user: dict = Depends(require_user)):
    return {"user": user}

@app.post("/api/user/profile")
async def save_user_profile(profile: UserProfile, user: dict = Depends(require_user)):
    profile_dict = profile.model_dump()
    res = UserService.save_profile(user["id"], profile_dict)
    return res

@app.get("/api/user/profile")
async def get_user_profile(user: dict = Depends(require_user)):
    profile = UserService.get_profile(user["id"])
    return {"profile": profile}

@app.post("/api/user/bookmarks/toggle")
async def toggle_bookmark(req: BookmarkRequest, user: dict = Depends(require_user)):
    res = UserService.toggle_bookmark(user["id"], req.scholarship_id)
    return res

@app.get("/api/user/bookmarks")
async def get_user_bookmarks(user: dict = Depends(require_user)):
    bookmarks = UserService.get_bookmarks(user["id"])
    return {"bookmarks": bookmarks}

@app.get("/")
async def root():
    index_file = static_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "ScholarAI Master's Scholarship Finder Backend Running. UI loading..."}

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "scholarships_indexed": len(SCHOLARSHIPS_DATABASE),
        "has_gemini_key": gemini_client.has_valid_key()
    }

@app.get("/api/api-key/status")
async def api_key_status():
    has_key = gemini_client.has_valid_key()
    source = "Dynamic / Environment" if has_key else "None"
    return ApiKeyStatus(has_key=has_key, source=source)

@app.post("/api/api-key/set")
async def set_api_key(req: ApiKeyRequest):
    if not req.api_key.strip():
        raise HTTPException(status_code=400, detail="API key cannot be empty")
    
    test_result = gemini_client.test_key(req.api_key)
    if not test_result.get("valid"):
        raise HTTPException(status_code=400, detail=f"Invalid Gemini API Key: {test_result.get('error')}")
    
    config.set_gemini_api_key(req.api_key)
    return {"success": True, "message": "Gemini API key verified and activated successfully!"}

@app.get("/api/scholarships")
async def list_scholarships():
    return SCHOLARSHIPS_DATABASE

@app.post("/api/profile/analyze")
async def analyze_profile(profile: UserProfile):
    summary = profile_agent.analyze_profile(profile)
    return summary

@app.post("/api/agent/discover")
async def discover_agent(profile: UserProfile):
    # Step 1: Profile Analysis Agent
    profile_summary = profile_agent.analyze_profile(profile)
    
    # Step 2: Discovery Agent (Curated + Live Search Grounding)
    discovery_res = discovery_agent.discover_scholarships(profile, profile_summary)
    
    # Step 3: Run preliminary suitability checks on top matches
    top_matches = discovery_res["matched_scholarships"]
    for s in top_matches[:5]:
        eval_result = eligibility_agent.evaluate(profile, s["id"], profile_summary)
        s["match_evaluation"] = eval_result.model_dump()

    return {
        "profile_summary": profile_summary,
        "matched_scholarships": top_matches,
        "ai_insights": discovery_res["ai_insights"],
        "search_grounded": discovery_res["search_grounded"]
    }

@app.post("/api/agent/evaluate")
async def evaluate_agent(req: RoadmapRequest):
    profile_summary = profile_agent.analyze_profile(req.profile)
    evaluation = eligibility_agent.evaluate(req.profile, req.scholarship_id, profile_summary)
    return evaluation

@app.post("/api/agent/roadmap")
async def roadmap_endpoint(req: RoadmapRequest):
    roadmap = roadmap_agent.generate_roadmap(req.profile, req.scholarship_id)
    return roadmap

@app.post("/api/agent/chat")
async def chat_endpoint(req: ChatRequest):
    reply = advisor_agent.reply(req.messages, profile=req.profile, scholarship_id=req.selected_scholarship_id)
    return {"reply": reply}
