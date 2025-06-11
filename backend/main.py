import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from jose import jwt, JWTError
import requests
from .database import users_collection # Import our MongoDB collection

# Load environment variables for local dev
from dotenv import load_dotenv
load_dotenv()

# --- Configuration & Models ---
app = FastAPI()
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")

# This is a startup check to fail fast if config is missing
if not CLERK_JWT_ISSUER:
    raise RuntimeError("FATAL ERROR: CLERK_JWT_ISSUER environment variable is not set.")

# This Pydantic model validates the incoming data from the frontend
class OnboardingData(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    headline: str
    primaryGoal: str
    preferredLanguages: List[str]
    branch: str
    selectedDomains: List[str]
    skillsToLearn: List[str] = []
    skillsToTeach: List[str] = []

# --- Authentication Dependency ---
# This function is the gatekeeper for our protected routes
async def get_current_user(request: Request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing or invalid")
    
    token = auth_header.split(" ")[1]
    
    try:
        jwks_url = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
        jwks = requests.get(jwks_url).json()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = next((key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]), None)
        
        if not rsa_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to find appropriate key")
            
        payload = jwt.decode(token, rsa_key, algorithms=["RS256"], issuer=CLERK_JWT_ISSUER)
        return payload
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")

# --- API Endpoints ---

@app.get("/api")
def read_root():
    return {"message": "Welcome to Learn N Teach API!"}

@app.post("/api/users/onboard", status_code=status.HTTP_201_CREATED)
async def onboard_user(data: OnboardingData, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.get("sub")
        
        # Robustly get email and name from Clerk payload
        email = current_user.get("email", "Not provided")
        name = current_user.get("name", "")
        if not name:
             name = f"{current_user.get('firstName', '')} {current_user.get('lastName', '')}".strip()

        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token.")

        # Check for duplicates before attempting to insert
        if users_collection.find_one({"userId": user_id}):
            # This user has already been onboarded.
            # Instead of an error, we can just return their existing data.
            return JSONResponse(status_code=200, content={"message": "User already onboarded."})
        if users_collection.find_one({"username": data.username}):
            raise HTTPException(status_code=400, detail="Username is already taken.")

        user_document = {
            "userId": user_id,
            "username": data.username,
            "email": email,
            "name": name,
            "headline": data.headline,
            "profilePictureUrl": current_user.get("imageUrl", ""),
            "points": 100,
            "badges": ["The Trailblazer"],
            "primaryGoal": data.primaryGoal,
            "preferredLanguages": data.preferredLanguages,
            "createdAt": datetime.utcnow(),
            "privateData": {"institutionName": "Not Provided", "location": "Not Provided"},
            "learningProfile": {
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
        user_document.pop('_id', None)
        return {"message": "Onboarding successful!", "user": user_document}
    
    except HTTPException as e:
        # Re-raise known HTTP exceptions
        raise e
    except Exception as e:
        # This is the crucial catch-all for unexpected crashes (e.g., DB is down)
        print(f"!!! FATAL ONBOARDING ERROR: {e}") # This will appear in your Vercel logs
        # And we return a clean JSON error, not an HTML page
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")