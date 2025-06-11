# backend/main.py (with heavy debugging)
import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from jose import jwt, JWTError
import requests
from .database import users_collection # This will print connection status on import

# --- Print statements to run ONCE when the server starts up ---
print("--- Cold Start: main.py is being loaded ---")
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")
if not CLERK_JWT_ISSUER:
    print("!!! FATAL: CLERK_JWT_ISSUER is NOT SET !!!")
else:
    print(f"✅ CLERK_JWT_ISSUER is set to: {CLERK_JWT_ISSUER}")

if users_collection is None:
    print("!!! FATAL: users_collection is None. Database connection failed. !!!")
else:
    print("✅ users_collection is available.")
# ---------------------------------------------------------------

app = FastAPI()

# Pydantic model and get_current_user function are the same...
class OnboardingData(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    headline: str
    primaryGoal: str
    preferredLanguages: List[str]
    branch: str
    selectedDomains: List[str]
    skillsToLearn: List[str] = []
    skillsToTeach: List[str] = []

async def get_current_user(request: Request):
    # ... (same as before)
    # This function is likely not the source of the error.
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing or invalid")
    token = auth_header.split(" ")[1]
    try:
        jwks_url = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
        jwks = requests.get(jwks_url).json()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = next((key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]), None)
        if not rsa_key: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to find appropriate key")
        payload = jwt.decode(token, rsa_key, algorithms=["RS256"], issuer=CLERK_JWT_ISSUER)
        return payload
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


@app.post("/api/users/onboard", status_code=status.HTTP_201_CREATED)
async def onboard_user(data: OnboardingData, current_user: dict = Depends(get_current_user)):
    print("--- 🚀 /api/users/onboard endpoint invoked ---")
    try:
        user_id = current_user.get("sub")
        print(f"Step 1: Extracted user_id: {user_id}")

        email = current_user.get("email_addresses", [None])[0]
        print(f"Step 2: Extracted email: {email}")

        if not user_id or not email:
            print("!!! ERROR: user_id or email is missing from the token.")
            raise HTTPException(status_code=400, detail="User ID or email not found in token.")

        print(f"Step 3: Checking for existing user with ID {user_id} or username {data.username}")
        if users_collection.find_one({"userId": user_id}):
            print("INFO: User already onboarded. Returning success.")
            return JSONResponse(status_code=200, content={"message": "User already onboarded."})
        if users_collection.find_one({"username": data.username}):
            print(f"!!! ERROR: Username {data.username} is taken.")
            raise HTTPException(status_code=400, detail="Username is already taken.")
        
        print("Step 4: Assembling user document for database insertion.")
        user_document = {
            # ... (the same user document as before)
            "userId": user_id, "username": data.username, "email": email, "name": current_user.get("name", "New User"), "headline": data.headline, "profilePictureUrl": current_user.get("imageUrl", ""), "points": 100, "badges": ["The Trailblazer"], "primaryGoal": data.primaryGoal, "preferredLanguages": data.preferredLanguages, "createdAt": datetime.utcnow(), "privateData": {"institutionName": "Not Provided", "location": "Not Provided"}, "learningProfile": {"branch": data.branch, "domains": data.selectedDomains, "skillsToLearn": data.skillsToLearn}, "tutorProfile": {"isTutor": len(data.skillsToTeach) > 0, "averageRating": 0, "totalSessionsTaught": 0, "teachableModules": []}
        }
        
        print("Step 5: Attempting to insert document into MongoDB...")
        users_collection.insert_one(user_document)
        print("✅ SUCCESS: Document inserted into MongoDB.")
        
        user_document.pop('_id', None)
        return {"message": "Onboarding successful!", "user": user_document}
    
    except Exception as e:
        print(f"!!! CATASTROPHIC ERROR in onboard_user: {type(e).__name__} - {e}")
        # This will now give us the exact error in the Vercel logs.
        raise HTTPException(status_code=500, detail=f"An internal server error occurred.")
    



@app.get("/api/users/onboarding-status")
async def get_onboarding_status(current_user: dict = Depends(get_current_user)):
    """
    Checks if a user has a profile in our database.
    This is the gatekeeper for the entire app.
    """
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token.")

    try:
        # We only need to check for existence, so we use a projection to be efficient
        user_profile = users_collection.find_one({"userId": user_id}, {"_id": 1})

        if user_profile:
            return {"status": "completed"}
        else:
            return {"status": "pending"}

    except Exception as e:
        print(f"!!! ERROR checking onboarding status: {e}")
        raise HTTPException(status_code=500, detail="Error checking user status.")
    

# Add this endpoint to your existing main.py file

class LearningTrack(BaseModel):
    skill: str
    skill_slug: str
    progress_summary: str
    progress_percent: int

class DashboardData(BaseModel):
    points: int
    isTutor: bool
    learningTracks: List[LearningTrack]

@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    """
    Fetches and aggregates all data needed for the main user dashboard.
    """
    username = current_user.get("username")
    if not username:
        raise HTTPException(status_code=403, detail="Username not found in token")

    try:
        user_profile = users_collection.find_one({"username": username})
        if not user_profile:
            # This should theoretically never be hit if the gatekeeper is working,
            # but it's good practice to have this check.
            raise HTTPException(status_code=404, detail="User profile not found.")

        # 1. Get points and tutor status
        points = user_profile.get("points", 0)
        is_tutor = user_profile.get("tutorProfile", {}).get("isTutor", False)

        # 2. Fetch and process learning roadmaps into learning tracks
        learning_tracks = []
        roadmaps_cursor = roadmaps_collection.find({"username": username})
        for roadmap in roadmaps_cursor:
            total_weeks = len(roadmap.get("weeklyPlan", []))
            completed_weeks = sum(1 for week in roadmap.get("weeklyPlan", []) if week.get("status") == "COMPLETED")
            
            progress_percent = (completed_weeks / total_weeks * 100) if total_weeks > 0 else 0
            
            learning_tracks.append({
                "skill": roadmap.get("skill"),
                "skill_slug": roadmap.get("skill").lower().replace(" ", "-"), # e.g., "Python for Data Science" -> "python-for-data-science"
                "progress_summary": f"{completed_weeks}/{total_weeks} Modules Complete",
                "progress_percent": int(progress_percent)
            })

        # Assemble the final data object
        dashboard_data = {
            "points": points,
            "isTutor": is_tutor,
            "learningTracks": learning_tracks
        }
        return dashboard_data

    except Exception as e:
        print(f"!!! ERROR fetching dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch dashboard data.")