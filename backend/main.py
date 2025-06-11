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