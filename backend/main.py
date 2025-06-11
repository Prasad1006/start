# backend/main.py

import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from jose import jwt, JWTError
import requests
from .database import users_collection # Import our MongoDB collection

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# --- Configuration & Models ---
app = FastAPI()
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")
if not CLERK_JWT_ISSUER:
    raise Exception("FATAL ERROR: CLERK_JWT_ISSUER environment variable is not set.")

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
# This is a reusable function to get the current user from the Clerk token
async def get_current_user(request: Request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing")

    token = auth_header.split(" ")[1]
    
    try:
        # Fetch the JWKS from Clerk to get the public key for verification
        jwks_url = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
        jwks = requests.get(jwks_url).json()
        
        # Decode and verify the token
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        if rsa_key:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                issuer=CLERK_JWT_ISSUER
            )
            # The 'sub' claim is the user's unique ID from Clerk
            return payload
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to find appropriate key")

    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")

# --- API Endpoints ---

@app.get("/api")
def read_root():
    return {"message": "Welcome to Learn N Teach API!"}

@app.post("/api/users/onboard", status_code=status.HTTP_201_CREATED)
async def onboard_user(data: OnboardingData, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("sub")
    email = current_user.get("primaryEmailAddress") or current_user.get("email") # Get email from token

    if not user_id or not email:
        raise HTTPException(status_code=400, detail="User ID or email not found in token.")

    # Check if a user with this Clerk ID or username already exists
    if users_collection.find_one({"userId": user_id}):
        raise HTTPException(status_code=400, detail="User profile already exists.")
    if users_collection.find_one({"username": data.username}):
        raise HTTPException(status_code=400, detail="Username is already taken.")

    # This is where we build the rich user document based on our schema
    user_document = {
        "userId": user_id,
        "username": data.username,
        "email": email,
        "name": current_user.get("firstName", ""), # Get name from Clerk token if available
        "headline": data.headline,
        "profilePictureUrl": current_user.get("imageUrl", ""),
        "points": 100, # Give bonus points for completing onboarding
        "badges": ["The Trailblazer"],
        "primaryGoal": data.primaryGoal,
        "preferredLanguages": data.preferredLanguages,
        "createdAt": datetime.utcnow(),
        "privateData": {
            "institutionName": "Not Provided", # Can be added later
            "location": "Not Provided"
        },
        "learningProfile": {
            "branch": data.branch,
            "domains": data.selectedDomains,
            "skillsToLearn": data.skillsToLearn
        },
        "tutorProfile": {
            "isTutor": len(data.skillsToTeach) > 0,
            "averageRating": 0,
            "totalSessionsTaught": 0,
            # We will only add modules here after they pass the eligibility quiz
            "teachableModules": [] 
        }
    }

    # Insert the new user document into the database
    try:
        result = users_collection.insert_one(user_document)
        user_document.pop('_id') # Don't send the ObjectId back
        return {"message": "Onboarding successful!", "user": user_document}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database insertion failed: {e}")