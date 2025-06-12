# backend/main.py (FINAL ARCHITECTURE)
from fastapi import FastAPI, Depends, HTTPException, status
from pymongo.database import Database
from typing import List
from datetime import datetime
from urllib.parse import quote

from . import workers, learning, auth
from .database import connect_to_mongo, close_mongo_connection, get_db_dependency
from .pydantic_models import OnboardingData, LearningTrack, DashboardData

app = FastAPI()
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

app.include_router(workers.router)
app.include_router(learning.router)

@app.post("/api/users/onboard", status_code=status.HTTP_201_CREATED)
async def onboard_user(data: OnboardingData, db: Database = Depends(get_db_dependency), current_user: dict = Depends(auth.get_current_user)):
    users_collection = db.users
    try:
        user_id = current_user.get("sub")
        if users_collection.find_one({"userId": user_id}): return {"message": "User already has a profile."}
        if users_collection.find_one({"username": data.username}): raise HTTPException(status_code=400, detail="Username is already taken.")
        user_doc = { "userId": user_id, "username": data.username, "email": current_user.get("email_addresses", [None])[0], "name": current_user.get("name") or f"{current_user.get('firstName', '')} {current_user.get('lastName', '')}".strip(), "headline": data.headline, "profilePictureUrl": current_user.get("imageUrl", ""), "points": 100, "badges": ["The Trailblazer"], "primaryGoal": data.primaryGoal, "preferredLanguages": data.preferredLanguages, "createdAt": datetime.utcnow(), "learningProfile": {"stream": data.stream, "branch": data.branch, "domains": data.selectedDomains, "skillsToLearn": data.skillsToLearn}, "tutorProfile": {"isTutor": len(data.skillsToTeach) > 0, "teachableModules": []} }
        users_collection.insert_one(user_doc)
        return {"message": "Onboarding successful!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.get("/api/users/onboarding-status")
async def get_onboarding_status(db: Database = Depends(get_db_dependency), current_user: dict = Depends(auth.get_current_user)):
    if db.users.find_one({"userId": current_user.get("sub")}, {"_id": 1}):
        return {"status": "completed"}
    return {"status": "pending"}

@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data(db: Database = Depends(get_db_dependency), current_user: dict = Depends(auth.get_current_user)):
    user_id, users_collection, roadmaps_collection = current_user.get("sub"), db.users, db.roadmaps
    user_profile = users_collection.find_one({"userId": user_id})
    if not user_profile: raise HTTPException(status_code=404, detail="User profile not found.")
    skills = user_profile.get("learningProfile", {}).get("skillsToLearn", [])
    gen_maps = {r["skill"]: r["skill_slug"] for r in roadmaps_collection.find({"userId": user_id}, {"skill": 1, "skill_slug": 1})}
    tracks = [ {"skill": s, "skill_slug": gen_maps.get(s, quote(s.lower().replace(" ", "-"), safe='')), "progress_summary": "Ready to Start" if s in gen_maps else "AI Roadmap Not Generated", "progress_percent": 0, "generated": s in gen_maps} for s in skills]
    return {"name": user_profile.get("name", ""), "points": user_profile.get("points", 0), "isTutor": user_profile.get("tutorProfile", {}).get("isTutor", False), "learningTracks": tracks}

@app.get("/api/profile")
async def get_my_profile(db: Database = Depends(get_db_dependency), current_user: dict = Depends(auth.get_current_user)):
    user_profile = db.users.find_one({"userId": current_user.get("sub")})
    if not user_profile: raise HTTPException(status_code=404, detail="Profile not found.")
    user_profile["_id"] = str(user_profile["_id"])
    return user_profile