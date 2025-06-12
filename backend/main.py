# backend/main.py (FINAL VERSION WITH BACKGROUND TASKS)
import os
import sys
import httpx
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request
from typing import List
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from urllib.parse import quote

# --- Module Imports ---
from . import workers, auth
from .database import users_collection, roadmaps_collection

load_dotenv()
app = FastAPI()

# --- Include Routers for Other Modules ---
# This makes endpoints defined in workers.py available
app.include_router(workers.router)
# Note: learning.py has been removed as its logic is now in this file.

# --- Pydantic Models ---
class OnboardingData(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    headline: str; primaryGoal: str; preferredLanguages: List[str]; stream: str; branch: str
    selectedDomains: List[str]; skillsToLearn: List[str] = []; skillsToTeach: List[str] = []

class LearningTrack(BaseModel):
    skill: str; skill_slug: str; progress_summary: str; progress_percent: int; generated: bool

class DashboardData(BaseModel):
    name: str; points: int; isTutor: bool; learningTracks: List[LearningTrack]


# --- Background Task Helper Function ---
async def trigger_worker(url: str, payload: dict, headers: dict):
    """Sends a non-blocking request to the worker endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload, headers=headers, timeout=10.0)
            print(f"✅ Background task dispatched to {url}", file=sys.stderr)
        except httpx.RequestError as e:
            print(f"!!! Error dispatching background task: {e}", file=sys.stderr)


# --- API Endpoints ---

@app.post("/api/roadmaps", status_code=202)
async def request_roadmap_generation(
    data: dict, 
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Accepts a user's request, immediately returns a '202 Accepted' response,
    and schedules the AI generation to run in the background. This prevents timeouts.
    """
    skill_name = data.get("skill")
    user_id = current_user.get("sub")
    if not skill_name: raise HTTPException(status_code=400, detail="Skill name is required.")

    # Get the secret key from environment to authorize the worker call.
    worker_secret = os.getenv("WORKER_SECRET_KEY")
    if not worker_secret:
        raise HTTPException(status_code=503, detail="Worker service is not configured on the server.")
    
    # Construct the full, absolute URL for the worker based on the incoming request.
    # This works reliably on both Vercel and localhost.
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    worker_url = f"{base_url}/api/workers/generate-roadmap"

    payload = {"userId": user_id, "skill": skill_name}
    headers = {"x-worker-secret": worker_secret}
    
    # Schedule the HTTP call to run after the response has been sent.
    background_tasks.add_task(trigger_worker, worker_url, payload, headers)
    
    return {"message": "Roadmap generation has been successfully scheduled."}


@app.post("/api/users/onboard", status_code=201)
async def onboard_user(data: OnboardingData, current_user: dict = Depends(auth.get_current_user)):
    if users_collection is None: raise HTTPException(status_code=503, detail="Database service unavailable.")
    user_id = current_user.get("sub")
    if users_collection.find_one({"userId": user_id}): return {"message": "User already has a profile."}
    if users_collection.find_one({"username": data.username}): raise HTTPException(status_code=400, detail="Username is already taken.")
    doc = { "userId": user_id, "username": data.username, "email": None, "name": current_user.get("name") or f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(), "headline": data.headline, "profilePictureUrl": current_user.get("picture", ""), "points": 100, "badges": ["The Trailblazer"], "primaryGoal": data.primaryGoal, "preferredLanguages": data.preferredLanguages, "createdAt": datetime.utcnow(), "learningProfile": {"stream": data.stream, "branch": data.branch, "domains": data.selectedDomains, "skillsToLearn": data.skillsToLearn}, "tutorProfile": {"isTutor": len(data.skillsToTeach) > 0, "teachableModules": []} }
    users_collection.insert_one(doc)
    return {"message": "Onboarding successful!"}


@app.get("/api/users/onboarding-status")
async def get_onboarding_status(current_user: dict = Depends(auth.get_current_user)):
    if users_collection is None: raise HTTPException(status_code=503, detail="Database service temporarily unavailable.")
    if users_collection.find_one({"userId": current_user.get("sub")}, {"_id": 1}):
        return {"status": "completed"}
    return {"status": "pending"}


@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data(current_user: dict = Depends(auth.get_current_user)):
    if users_collection is None or roadmaps_collection is None: raise HTTPException(status_code=503, detail="Database service temporarily unavailable.")
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