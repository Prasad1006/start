# backend/main.py (FINAL ROBUST VERSION)
import os
import sys
from fastapi import FastAPI, Depends, HTTPException, status
from pymongo.database import Database
from typing import List
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from urllib.parse import quote

# --- Module Imports ---
from . import workers, learning, auth, cron
from .database import connect_to_mongo, close_mongo_connection, get_db_dependency

# --- App & Lifespan ---
app = FastAPI()
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

app.include_router(workers.router)
app.include_router(learning.router)

# --- Pydantic Models (Moved back for simplicity) ---
class OnboardingData(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    headline: str; primaryGoal: str; preferredLanguages: List[str]; stream: str; branch: str
    selectedDomains: List[str]; skillsToLearn: List[str] = []; skillsToTeach: List[str] = []

class LearningTrack(BaseModel):
    skill: str; skill_slug: str; progress_summary: str; progress_percent: int; generated: bool

class DashboardData(BaseModel):
    name: str; points: int; isTutor: bool; learningTracks: List[LearningTrack]


# --- API Endpoints ---
@app.post("/api/users/onboard", status_code=status.HTTP_201_CREATED)
async def onboard_user(data: OnboardingData, db: Database = Depends(get_db_dependency), current_user: dict = Depends(auth.get_current_user)):
    users_collection = db.users
    try:
        user_id = current_user.get("sub")
        if users_collection.find_one({"userId": user_id}): return {"message": "User already has a profile."}
        if users_collection.find_one({"username": data.username}): raise HTTPException(status_code=400, detail="Username is already taken.")
        
        user_doc = { "userId": user_id, "username": data.username, "email": current_user.get("email_addresses", [None])[0], "name": current_user.get("name") or f"{current_user.get('firstName', '')} {current_user.get('lastName', '')}".strip(), "headline": data.headline, "profilePictureUrl": current_user.get("imageUrl", ""), "points": 100, "badges": ["The Trailblazer"], "primaryGoal": data.primaryGoal, "preferredLanguages": data.preferredLanguages, "createdAt": datetime.utcnow(), "learningProfile": {"stream": data.stream, "branch": data.branch, "domains": data.selectedDomains, "skillsToLearn": data.skillsToLearn}, "tutorProfile": {"isTutor": len(data.skillsToTeach) > 0, "teachableModules": []} }
        
        result = users_collection.insert_one(user_doc)
        
        if not result.inserted_id:
            raise Exception("Failed to insert user document into the database.")
            
        return {"message": "Onboarding successful!"}

    except HTTPException as e:
        # Re-raise HTTPExceptions directly as they are safe
        raise e
    except Exception as e:
        # --- ROBUST ERROR LOGGING ---
        # For any other unexpected error, log it clearly and return a generic, safe JSON response.
        print(f"!!! CRITICAL ERROR IN /api/users/onboard: {e}", file=sys.stderr)
        # Don't try to format the exception 'e'. Just return a safe, valid JSON object.
        raise HTTPException(status_code=500, detail="An internal server error occurred during profile creation.")


# ... The rest of the functions (get_onboarding_status, get_dashboard, get_my_profile)
#     can remain exactly as they were in the previous "final" version. Their logic is sound.

@app.get("/api/users/onboarding-status")
async def get_onboarding_status(db: Database = Depends(get_db_dependency), current_user: dict = Depends(auth.get_current_user)):
    if db.users.find_one({"userId": current_user.get("sub")}, {"_id": 1}): return {"status": "completed"}
    return {"status": "pending"}

@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data(db: Database = Depends(get_db_dependency), current_user: dict = Depends(auth.get_current_user)):
    user_id = current_user.get("sub"); users = db.users; roadmaps = db.roadmaps
    profile = users.find_one({"userId": user_id})
    if not profile: raise HTTPException(status_code=404, detail="User profile not found.")
    skills = profile.get("learningProfile", {}).get("skillsToLearn", [])
    gen_maps = {r["skill"]: r["skill_slug"] for r in roadmaps.find({"userId": user_id}, {"skill": 1, "skill_slug": 1})}
    tracks = [ {"skill": s, "skill_slug": gen_maps.get(s, quote(s.lower().replace(" ", "-"), safe='')), "progress_summary": "Ready to Start" if s in gen_maps else "AI Roadmap Not Generated", "progress_percent": 0, "generated": s in gen_maps} for s in skills]
    return {"name": profile.get("name", ""), "points": profile.get("points", 0), "isTutor": profile.get("tutorProfile", {}).get("isTutor", False), "learningTracks": tracks}

@app.get("/api/profile")
async def get_my_profile(db: Database = Depends(get_db_dependency), current_user: dict = Depends(auth.get_current_user)):
    profile = db.users.find_one({"userId": current_user.get("sub")})
    if not profile: raise HTTPException(status_code=404, detail="Profile not found.")
    profile["_id"] = str(profile["_id"])
    return profile