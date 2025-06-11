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
# This part runs once when the serverless function starts (cold start)
print("--- Python script cold start ---", file=sys.stderr)
load_dotenv()
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")

try:
    # Attempt to import the database collections
    from .database import users_collection, roadmaps_collection
    if users_collection is None:
        # This will happen if the connection string in database.py failed
        raise ImportError("Database connection failed, users_collection is None.")
    print("✅ Database collections imported successfully.", file=sys.stderr)
except ImportError as e:
    print(f"!!! FATAL: Could not import database collections: {e}", file=sys.stderr)
    users_collection = None # Ensure it's None if import fails to prevent further errors

# Initialize the FastAPI app
app = FastAPI()

# --- Pydantic Models (Defines the shape of our data) ---

class OnboardingData(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    headline: str
    primaryGoal: str
    preferredLanguages: List[str]
    stream: str # This was the missing piece
    branch: str
    selectedDomains: List[str]
    skillsToLearn: List[str] = []
    skillsToTeach: List[str] = []

class LearningTrack(BaseModel):
    skill: str
    skill_slug: str
    progress_summary: str
    progress_percent: int

class DashboardData(BaseModel):
    name: str
    points: int
    isTutor: bool
    learningTracks: List[LearningTrack]

# --- Authentication Dependency ---
# This function acts as a gatekeeper for our protected API routes.
async def get_current_user(request: Request):
    if not CLERK_JWT_ISSUER:
        raise HTTPException(status_code=500, detail="JWT Issuer not configured.")
        
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or malformed")
    
    token = auth_header.split(" ")[1]
    
    try:
        # Fetch the public keys from Clerk to verify the token
        jwks_url = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
        jwks = requests.get(jwks_url).json()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = next((key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]), None)
        
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Unable to find appropriate key in JWKS")
            
        # Decode and verify the token's signature and claims
        payload = jwt.decode(token, rsa_key, algorithms=["RS256"], issuer=CLERK_JWT_ISSUER)
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during token validation: {e}")


# --- API Endpoints ---

@app.post("/api/users/onboard", status_code=status.HTTP_201_CREATED)
async def onboard_user(data: OnboardingData, current_user: dict = Depends(get_current_user)):
    """
    Handles the final step of user onboarding. Creates a new user profile in the database.
    """
    if users_collection is None:
        return JSONResponse(status_code=503, content={"error": "Database service is not available."})
    
    try:
        user_id = current_user.get("sub")
        if not user_id:
            return JSONResponse(status_code=400, content={"error": "User ID not found in token."})

        # Check for duplicates to prevent errors
        if users_collection.find_one({"userId": user_id}):
            return JSONResponse(status_code=200, content={"message": "User already has a profile."})
        if users_collection.find_one({"username": data.username}):
            return JSONResponse(status_code=400, content={"error": "Username is already taken."})
        
        # Assemble the complete user document based on our database schema
        user_document = {
            "userId": user_id,
            "username": data.username,
            "email": current_user.get("email_addresses", [None])[0],
            "name": current_user.get("name") or f"{current_user.get('firstName', '')} {current_user.get('lastName', '')}".strip(),
            "headline": data.headline,
            "profilePictureUrl": current_user.get("imageUrl", ""),
            "points": 100,
            "badges": ["The Trailblazer"],
            "primaryGoal": data.primaryGoal,
            "preferredLanguages": data.preferredLanguages,
            "createdAt": datetime.utcnow(),
            "learningProfile": {
                "stream": data.stream,
                "branch": data.branch,
                "domains": data.selectedDomains,
                "skillsToLearn": data.skillsToLearn
            },
            "tutorProfile": {
                "isTutor": len(data.skillsToTeach) > 0,
                "averageRating": 0,
                "totalSessionsTaught": 0,
                "teachableModules": []
            }
        }
        
        users_collection.insert_one(user_document)
        return {"message": "Onboarding successful!"}
    
    except Exception as e:
        print(f"!!! ONBOARDING CRASH: {type(e).__name__} - {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return JSONResponse(
            status_code=500,
            content={"error": "An internal server error occurred during onboarding."}
        )

@app.get("/api/users/onboarding-status")
async def get_onboarding_status(current_user: dict = Depends(get_current_user)):
    """
    Checks if a user has completed onboarding. This is the 'gatekeeper' endpoint.
    """
    if users_collection and users_collection.find_one({"userId": current_user.get("sub")}, {"_id": 1}):
        return {"status": "completed"}
    return {"status": "pending"}

@app.get("/api/profile")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    Fetches the full profile for the currently logged-in user.
    """
    if users_collection is None:
        raise HTTPException(status_code=503, detail="Database service unavailable.")
    
    user_profile = users_collection.find_one({"userId": current_user.get("sub")})
    if not user_profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    
    user_profile["_id"] = str(user_profile["_id"]) # Convert MongoDB ObjectId to string for JSON
    return user_profile

@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    """
    Fetches and aggregates all data needed for the main user dashboard.
    """
    if users_collection is None:
        raise HTTPException(status_code=503, detail="Database service unavailable.")

    user_profile = users_collection.find_one({"userId": current_user.get("sub")})
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found. Please try logging in again.")

    return {
        "name": user_profile.get("name", ""),
        "points": user_profile.get("points", 0),
        "isTutor": user_profile.get("tutorProfile", {}).get("isTutor", False),
        "learningTracks": [] # This is a placeholder until roadmaps are built in a later phase
    }