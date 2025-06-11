import os
import sys
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from jose import jwt, JWTError
import requests
from dotenv import load_dotenv

# --- Startup & Database Import ---
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

# --- Pydantic Models (Data Validation) ---
class OnboardingData(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    headline: str; primaryGoal: str; preferredLanguages: List[str]; branch: str
    selectedDomains: List[str]; skillsToLearn: List[str] = []; skillsToTeach: List[str] = []

class LearningTrack(BaseModel):
    skill: str; skill_slug: str; progress_summary: str; progress_percent: int

class DashboardData(BaseModel):
    points: int; isTutor: bool; learningTracks: List[LearningTrack]

# --- Authentication Dependency ---
async def get_current_user(request: Request):
    if not CLERK_JWT_ISSUER:
        raise HTTPException(status_code=500, detail="JWT Issuer not configured.")
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or malformed")
    token = auth_header.split(" ")[1]
    try:
        jwks_url = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
        jwks = requests.get(jwks_url).json()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = next((key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]), None)
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Unable to find appropriate key in JWKS")
        return jwt.decode(token, rsa_key, algorithms=["RS256"], issuer=CLERK_JWT_ISSUER)
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

# --- API Endpoints ---

@app.post("/api/users/onboard", status_code=status.HTTP_201_CREATED)
async def onboard_user(data: OnboardingData, current_user: dict = Depends(get_current_user)):
    try:
        if users_collection is None:
            raise Exception("Database service is not available.")
            
        user_id = current_user.get("sub")
        email = current_user.get("email_addresses", [None])[0]
        if not user_id or not email:
            return JSONResponse(status_code=400, content={"error": "User ID or email missing in token."})

        if users_collection.find_one({"userId": user_id}):
            return JSONResponse(status_code=200, content={"message": "User already has a profile."})
        if users_collection.find_one({"username": data.username}):
            return JSONResponse(status_code=400, content={"error": "Username is already taken."})
        
        user_document = {
            "userId": user_id, "username": data.username, "email": email,
            "name": current_user.get("name") or f"{current_user.get('firstName', '')} {current_user.get('lastName', '')}".strip(),
            "headline": data.headline, "profilePictureUrl": current_user.get("imageUrl", ""),
            "points": 100, "badges": ["The Trailblazer"], "primaryGoal": data.primaryGoal,
            "preferredLanguages": data.preferredLanguages, "createdAt": datetime.utcnow(),
            "learningProfile": {"branch": data.branch, "domains": data.selectedDomains, "skillsToLearn": data.skillsToLearn},
            "tutorProfile": {"isTutor": len(data.skillsToTeach) > 0, "teachableModules": []}
        }
        
        users_collection.insert_one(user_document)
        user_document.pop('_id', None)
        return {"message": "Onboarding successful!", "user": user_document}
    
    except Exception as e:
        print(f"!!! CATASTROPHIC ERROR in onboard_user: {e}", file=sys.stderr)
        return JSONResponse(status_code=500, content={"error": "An internal server error occurred."})

@app.get("/api/users/onboarding-status")
async def get_onboarding_status(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("sub")
    if users_collection and users_collection.find_one({"userId": user_id}, {"_id": 1}):
        return {"status": "completed"}
    return {"status": "pending"}

@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    username = current_user.get("username")
    if not username: raise HTTPException(status_code=403, detail="Username not found")
    try:
        user_profile = users_collection.find_one({"username": username})
        if not user_profile: raise HTTPException(status_code=404, detail="User profile not found")
        
        points = user_profile.get("points", 0)
        is_tutor = user_profile.get("tutorProfile", {}).get("isTutor", False)
        learning_tracks = [] # Placeholder until roadmaps are built
        
        return {"points": points, "isTutor": is_tutor, "learningTracks": learning_tracks}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not fetch dashboard data.")