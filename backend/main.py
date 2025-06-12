import os
import sys
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from jose import jwt, JWTError
import requests
from dotenv import load_dotenv

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

app = FastAPI()

# --- Pydantic Models ---
class OnboardingData(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    headline: str; primaryGoal: str; preferredLanguages: List[str]; stream: str; branch: str
    selectedDomains: List[str]; skillsToLearn: List[str] = []; skillsToTeach: List[str] = []

class LearningTrack(BaseModel):
    skill: str; skill_slug: str; progress_summary: str; progress_percent: int

class DashboardData(BaseModel):
    name: str; points: int; isTutor: bool; learningTracks: List[LearningTrack]

# --- Auth Dependency ---
async def get_current_user(request: Request):
    if not CLERK_JWT_ISSUER: raise HTTPException(status_code=500, detail="JWT Issuer not configured.")
    token = request.headers.get('Authorization', '').split(' ')[-1]
    try:
        jwks = requests.get(f"{CLERK_JWT_ISSUER}/.well-known/jwks.json").json()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = next((key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]), None)
        if not rsa_key: raise HTTPException(status_code=401, detail="Key not found")
        return jwt.decode(token, rsa_key, algorithms=["RS256"], issuer=CLERK_JWT_ISSUER)
    except (JWTError, IndexError) as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

# --- API Endpoints ---
@app.post("/api/users/onboard", status_code=status.HTTP_201_CREATED)
async def onboard_user(data: OnboardingData, current_user: dict = Depends(get_current_user)):
    # ... (Onboarding logic from previous answer - no changes needed here) ...
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
    # ... (Gatekeeper logic - no changes needed) ...
    if users_collection and users_collection.find_one({"userId": current_user.get("sub")}, {"_id": 1}):
        return {"status": "completed"}
    return {"status": "pending"}

@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    # ... (Dashboard logic - no changes needed) ...
    user_profile = users_collection.find_one({"userId": current_user.get("sub")})
    if not user_profile: raise HTTPException(status_code=404, detail="User profile not found.")
    return {
        "name": user_profile.get("name", ""),
        "points": user_profile.get("points", 0),
        "isTutor": user_profile.get("tutorProfile", {}).get("isTutor", False),
        "learningTracks": []
    }

# ** THIS IS THE CORRECTED AND FINAL VERSION OF THE PROFILE ENDPOINT **
@app.get("/api/profile")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    Fetches the full profile for the currently logged-in user using their unique ID.
    """
    if users_collection is None:
        raise HTTPException(status_code=503, detail="Database service unavailable.")
    
    # Use the unique user ID from the token for the most reliable lookup.
    user_id = current_user.get("sub")
    
    # Find the user document in the database by their unique Clerk ID.
    user_profile = users_collection.find_one({"userId": user_id})
    
    if not user_profile:
        # This can happen if the user exists in Clerk but their onboarding failed.
        # The gatekeeper should prevent this, but it's a good safety check.
        raise HTTPException(status_code=404, detail="Profile not found in our database. Please complete onboarding.")
    
    # Convert MongoDB's binary ObjectId to a string so it can be sent as JSON.
    user_profile["_id"] = str(user_profile["_id"])
    
    return user_profile