import os
from fastapi import FastAPI, Depends, HTTPException, status
from typing import List
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from urllib.parse import quote

from . import auth
from .database import users_collection, roadmaps_collection
from .tasks import generate_roadmap_task

load_dotenv()
app = FastAPI()

class OnboardingData(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    headline: str; primaryGoal: str; preferredLanguages: List[str]; stream: str; branch: str
    selectedDomains: List[str]; skillsToLearn: List[str] = []; skillsToTeach: List[str] = []

class LearningTrack(BaseModel):
    skill: str; skill_slug: str; progress_summary: str; progress_percent: int; generated: bool

class DashboardData(BaseModel):
    name: str; points: int; isTutor: bool; learningTracks: List[LearningTrack]

@app.post("/api/roadmaps", status_code=202)
async def request_roadmap(data: dict, current_user: dict = Depends(auth.get_current_user)):
    skill_name, user_id = data.get("skill"), current_user.get("sub")
    if not skill_name: raise HTTPException(status_code=400, detail="Skill name is required.")
    
    generate_roadmap_task.send(user_id, skill_name)
    return {"message": "Roadmap generation has been scheduled."}

@app.post("/api/users/onboard", status_code=201)
async def onboard_user(data: OnboardingData, current_user: dict = Depends(auth.get_current_user)):
    if users_collection is None: raise HTTPException(status_code=503, detail="Database unavailable.")
    user_id = current_user.get("sub")
    if users_collection.find_one({"userId": user_id}): return {"message": "User already has profile."}
    if users_collection.find_one({"username": data.username}): raise HTTPException(400, "Username taken.")
    doc = {"userId": user_id, "username": data.username, "name": current_user.get("name") or f"{current_user.get('first_name','')} {current_user.get('last_name','')}".strip(), "headline": data.headline, "profilePictureUrl": current_user.get("picture", ""), "points": 100, "badges": ["The Trailblazer"], "primaryGoal": data.primaryGoal, "preferredLanguages": data.preferredLanguages, "createdAt": datetime.utcnow(), "learningProfile": {"stream": data.stream, "branch": data.branch, "domains": data.selectedDomains, "skillsToLearn": data.skillsToLearn}, "tutorProfile": {"isTutor": len(data.skillsToTeach) > 0, "teachableModules": []}}
    users_collection.insert_one(doc)
    return {"message": "Onboarding successful!"}

@app.get("/api/users/onboarding-status")
async def get_onboarding_status(current_user: dict = Depends(auth.get_current_user)):
    if users_collection is None: raise HTTPException(503, "Database unavailable.")
    if users_collection.find_one({"userId": current_user.get("sub")}, {"_id": 1}):
        return {"status": "completed"}
    return {"status": "pending"}


@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data(current_user: dict = Depends(auth.get_current_user)):
    # Defensive check at the very top
    if users_collection is None: 
        raise HTTPException(status_code=503, detail="Database connection failed.")

    user_id = current_user.get("sub")
    profile = users_collection.find_one({"userId": user_id})
    if not profile:
        # This can happen if the user's onboarding is in progress.
        # Returning a 404 is correct, but let's give a clear message.
        raise HTTPException(status_code=404, detail="User profile not yet fully created. Please wait or complete onboarding.")

    skills_to_learn = profile.get("learningProfile", {}).get("skillsToLearn", [])
    
    # --- START OF THE FIX ---
    generated_roadmaps = []
    if roadmaps_collection: # Check if the collection itself exists
        # Find all roadmaps for this user. This returns a cursor.
        cursor = roadmaps_collection.find({"userId": user_id})
        # Safely iterate through the cursor. If it's empty, this loop doesn't run.
        generated_roadmaps = list(cursor)

    # Create a dictionary to easily look up if a roadmap for a skill exists.
    # We now safely check if 'skill' and 'skill_slug' exist in each document.
    generated_skills_map = {
        r.get("skill"): r.get("skill_slug") 
        for r in generated_roadmaps 
        if r.get("skill") and r.get("skill_slug")
    }

    learning_tracks = []
    for skill in skills_to_learn:
        is_generated = skill in generated_skills_map
        slug = generated_skills_map.get(skill) if is_generated else quote(skill.lower().replace(" ", "-").replace("/", "-"), safe='')
        
        learning_tracks.append({
            "skill": skill,
            "skill_slug": slug,
            "progress_summary": "Ready to Start" if is_generated else "AI Roadmap Not Generated",
            "progress_percent": 0,
            "generated": is_generated
        })
    # --- END OF THE FIX ---

    return {
        "name": profile.get("name", ""),
        "points": profile.get("points", 0),
        "isTutor": profile.get("tutorProfile", {}).get("isTutor", False),
        "learningTracks": learning_tracks
    }

@app.get("/api/profile")
async def get_my_profile(current_user: dict = Depends(auth.get_current_user)):
    if users_collection is None: raise HTTPException(503, "Database unavailable.")
    profile = users_collection.find_one({"userId": current_user.get("sub")})
    if not profile: raise HTTPException(404, "Profile not found.")
    profile["_id"] = str(profile["_id"])
    return profile