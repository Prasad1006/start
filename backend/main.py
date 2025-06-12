# backend/main.py (FINAL VERSION WITH CORRECTED JWT CLAIMS)
import os
from fastapi import FastAPI, Depends, HTTPException, status
from typing import List
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from urllib.parse import quote

# --- Module Imports ---
from . import workers, learning, auth
from .database import users_collection, roadmaps_collection

load_dotenv()
app = FastAPI()

# --- Include Routers ---
app.include_router(workers.router)
app.include_router(learning.router)

# --- Pydantic Models ---
class OnboardingData(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    headline: str; primaryGoal: str; preferredLanguages: List[str]; stream: str; branch: str
    selectedDomains: List[str]; skillsToLearn: List[str] = []; skillsToTeach: List[str] = []

class LearningTrack(BaseModel):
    skill: str; skill_slug: str; progress_summary: str; progress_percent: int; generated: bool

class DashboardData(BaseModel):
    name: str; points: int; isTutor: bool; learningTracks: List[LearningTrack]

# --- API Endpoints ---
@app.post("/api/users/onboard", status_code=201)
async def onboard_user(data: OnboardingData, current_user: dict = Depends(auth.get_current_user)):
    if users_collection is None: raise HTTPException(status_code=503, detail="Database service unavailable.")
    
    # --- CORRECT JWT PAYLOAD ACCESS ---
    user_id = current_user.get("sub")
    name = current_user.get("name") # `name` is often a top-level claim
    first_name = current_user.get("first_name")
    last_name = current_user.get("last_name")
    image_url = current_user.get("picture") # The URL is in the 'picture' claim
    
    # Clerk does not guarantee a top-level email claim.
    # We use the 'user_id' for lookup as it's the most reliable unique identifier.
    # An email can be fetched separately if needed but is not required for this document.
    
    if users_collection.find_one({"userId": user_id}): return {"message": "User already has a profile."}
    if users_collection.find_one({"username": data.username}): raise HTTPException(status_code=400, detail="Username is already taken.")
    
    user_doc = { 
        "userId": user_id, 
        "username": data.username,
        "email": None, # Email is not reliably available in the standard token, can be updated later
        "name": name or f"{first_name or ''} {last_name or ''}".strip(), 
        "headline": data.headline, 
        "profilePictureUrl": image_url, 
        "points": 100, "badges": ["The Trailblazer"], 
        "primaryGoal": data.primaryGoal, "preferredLanguages": data.preferredLanguages, 
        "createdAt": datetime.utcnow(), 
        "learningProfile": {"stream": data.stream, "branch": data.branch, "domains": data.selectedDomains, "skillsToLearn": data.skillsToLearn}, 
        "tutorProfile": {"isTutor": len(data.skillsToTeach) > 0, "teachableModules": []} 
    }
    users_collection.insert_one(user_doc)
    return {"message": "Onboarding successful!"}

@app.get("/api/users/onboarding-status")
async def get_onboarding_status(current_user: dict = Depends(auth.get_current_user)):
    if users_collection is None: raise HTTPException(status_code=503, detail="Database service unavailable.")
    if users_collection.find_one({"userId": current_user.get("sub")}, {"_id": 1}):
        return {"status": "completed"}
    return {"status": "pending"}

@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data(current_user: dict = Depends(auth.get_current_user)):
    if users_collection is None or roadmaps_collection is None: raise HTTPException(status_code=503, detail="Database service unavailable.")
    user_id = current_user.get("sub")
    profile = users_collection.find_one({"userId": user_id})
    if not profile: raise HTTPException(status_code=404, detail="User profile not found.")
    skills = profile.get("learningProfile", {}).get("skillsToLearn", [])
    gen_maps = {r["skill"]: r["skill_slug"] for r in roadmaps_collection.find({"userId": user_id}, {"skill": 1, "skill_slug": 1})}
    tracks = [{"skill": s, "skill_slug": gen_maps.get(s, quote(s.lower().replace(" ", "-"), safe='')), "progress_summary": "Ready to Start" if s in gen_maps else "AI Roadmap Not Generated", "progress_percent": 0, "generated": s in gen_maps} for s in skills]
    return {"name": profile.get("name", ""), "points": profile.get("points", 0), "isTutor": profile.get("tutorProfile", {}).get("isTutor", False), "learningTracks": tracks}

@app.get("/api/profile")
async def get_my_profile(current_user: dict = Depends(auth.get_current_user)):
    if users_collection is None: raise HTTPException(status_code=503, detail="Database service unavailable.")
    profile = users_collection.find_one({"userId": current_user.get("sub")})
    if not profile: raise HTTPException(status_code=404, detail="Profile not found.")
    profile["_id"] = str(profile["_id"])
    return profile