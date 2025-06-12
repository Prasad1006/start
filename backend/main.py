# backend/main.py (fully updated version)
import os
import sys
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from dotenv import load_dotenv

# --- Our module imports ---
from . import workers
from . import learning
from .auth import get_current_user # <<< THIS IS THE FIX. Import from auth.py

# --- Startup & Database Initialization ---
load_dotenv()
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")

try:
    from .database import users_collection, roadmaps_collection
    if users_collection is None:
        raise ImportError("Database connection failed, users_collection is None.")
except ImportError as e:
    print(f"!!! FATAL: Could not import database collections: {e}", file=sys.stderr)
    users_collection = None
    roadmaps_collection = None

app = FastAPI()

# --- Include the new routers ---
app.include_router(workers.router)
app.include_router(learning.router)

# --- Pydantic Models (Unchanged) ---
class OnboardingData(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    headline: str; primaryGoal: str; preferredLanguages: List[str]; stream: str; branch: str
    selectedDomains: List[str]; skillsToLearn: List[str] = []; skillsToTeach: List[str] = []

class LearningTrack(BaseModel):
    skill: str
    skill_slug: str
    progress_summary: str
    progress_percent: int
    generated: bool

class DashboardData(BaseModel):
    name: str
    points: int
    isTutor: bool
    learningTracks: List[LearningTrack]

# --- Auth Dependency is now REMOVED from this file ---
# It has been moved to backend/auth.py

# --- API Endpoints ---
@app.post("/api/users/onboard", status_code=status.HTTP_201_CREATED)
async def onboard_user(data: OnboardingData, current_user: dict = Depends(get_current_user)):
    # ... (This logic is correct and remains unchanged) ...
    if users_collection is None:
        return JSONResponse(status_code=503, content={"error": "Database service is not available."})
    try:
        user_id = current_user.get("sub")
        if users_collection.find_one({"userId": user_id}):
            return JSONResponse(status_code=200, content={"message": "User already has a profile."})
        if users_collection.find_one({"username": data.username}):
            return JSONResponse(status_code=400, content={"error": "Username is already taken."})
        user_document = {
            "userId": user_id, "username": data.username, "email": current_user.get("email_addresses", [None])[0],
            "name": current_user.get("name") or f"{current_user.get('firstName', '')} {current_user.get('lastName', '')}".strip(),
            "headline": data.headline, "profilePictureUrl": current_user.get("imageUrl", ""),
            "points": 100, "badges": ["The Trailblazer"], "primaryGoal": data.primaryGoal,
            "preferredLanguages": data.preferredLanguages, "createdAt": datetime.utcnow(),
            "learningProfile": {"stream": data.stream, "branch": data.branch, "domains": data.selectedDomains, "skillsToLearn": data.skillsToLearn},
            "tutorProfile": {"isTutor": len(data.skillsToTeach) > 0, "teachableModules": []}
        }
        users_collection.insert_one(user_document)
        return {"message": "Onboarding successful!"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "An internal server error occurred during onboarding."})


@app.get("/api/users/onboarding-status")
async def get_onboarding_status(current_user: dict = Depends(get_current_user)):
    # ... (Unchanged) ...
    if users_collection and users_collection.find_one({"userId": current_user.get("sub")}, {"_id": 1}):
        return {"status": "completed"}
    return {"status": "pending"}

@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    # ... (This logic is correct and remains unchanged) ...
    user_id = current_user.get("sub")
    user_profile = users_collection.find_one({"userId": user_id})
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found. Please complete onboarding.")

    skills_to_learn = user_profile.get("learningProfile", {}).get("skillsToLearn", [])
    generated_roadmaps = list(roadmaps_collection.find({"userId": user_id}, {"skill": 1, "skill_slug": 1}))
    generated_skills = {r["skill"]: r["skill_slug"] for r in generated_roadmaps}

    learning_tracks = []
    for skill in skills_to_learn:
        is_generated = skill in generated_skills
        slug = generated_skills.get(skill, "") if is_generated else skill.lower().replace(" ", "-").replace("/", "-").replace(".", "")
        
        learning_tracks.append({
            "skill": skill,
            "skill_slug": slug,
            "progress_summary": "Ready to Start" if is_generated else "AI Roadmap Not Generated",
            "progress_percent": 0,
            "generated": is_generated
        })

    return {
        "name": user_profile.get("name", ""),
        "points": user_profile.get("points", 0),
        "isTutor": user_profile.get("tutorProfile", {}).get("isTutor", False),
        "learningTracks": learning_tracks
    }

@app.get("/api/profile")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    # ... (Unchanged) ...
    if users_collection is None: raise HTTPException(status_code=503, detail="Database service unavailable.")
    user_id = current_user.get("sub")
    user_profile = users_collection.find_one({"userId": user_id})
    if not user_profile: raise HTTPException(status_code=404, detail="Profile not found in our database. Please complete onboarding.")
    user_profile["_id"] = str(user_profile["_id"])
    return user_profile