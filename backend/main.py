# backend/main.py (SECURE VERSION)

import os
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from jose import jwt, JWTError
import requests

# Import our database connection
from .database import users_collection

# Clerk SDK for getting user email
import clerk_client
from clerk_client.api import users_api

# Load environment variables for local development
from dotenv import load_dotenv
load_dotenv()

# --- Configuration ---
app = FastAPI()
CLERK_API_KEY = os.getenv("CLERK_API_KEY")
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")

if not CLERK_API_KEY:
    raise Exception("CLERK_API_KEY not found in environment variables")
if not CLERK_JWT_ISSUER:
    raise Exception("CLERK_JWT_ISSUER not found in environment variables")

clerk_client.configuration.api_key['Authorization'] = CLERK_API_KEY

# This is a standard FastAPI pattern for extracting a Bearer token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Authentication Dependency ---

# Fetch the public keys from Clerk's JWKS endpoint ONCE when the app starts.
# This is much more efficient than fetching it on every request.
JWKS_URL = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
try:
    jwks = requests.get(JWKS_URL).json()
except requests.exceptions.RequestException as e:
    print(f"Error fetching JWKS: {e}")
    jwks = {}

async def get_user_id_from_token(token: str = Depends(oauth2_scheme)) -> str:
    """
    This is our security guard. It decodes and verifies the JWT token from the
    Authorization header and returns the user's ID (the 'sub' claim).
    If the token is invalid in any way, it raises an HTTPException.
    """
    try:
        # Decode the token using the public keys from Clerk
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            issuer=CLERK_JWT_ISSUER,
            options={"verify_aud": False} # Audience verification is not typically needed for this flow
        )
        # The 'sub' (subject) claim in the token is the user's ID
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID not found in token")
        return user_id
    except JWTError as e:
        # This will catch expired tokens, invalid signatures, etc.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- Pydantic Models for Data Validation ---

class OnboardingData(BaseModel):
    # We no longer need authUserId in the body, as we get it securely from the token.
    username: str
    name: str
    headline: str
    primaryGoal: str
    preferredLanguages: List[str]
    institutionName: Optional[str] = None
    location: Optional[str] = None

# --- API Endpoints ---

@app.get("/api/health")
def read_root():
    return {"status": "ok", "message": "Backend is healthy!"}

# Notice the 'Depends' here. This endpoint is now PROTECTED.
# It can only be accessed with a valid token.
@app.post("/api/users/onboard")
async def onboard_user(data: OnboardingData, auth_user_id: str = Depends(get_user_id_from_token)):
    """
    Creates a new user profile in the database.
    The auth_user_id is now securely provided by our dependency, not the client.
    """
    if not users_collection:
         raise HTTPException(status_code=503, detail="Database not available")
         
    # 1. Check if a user with this authUserId already exists
    if users_collection.find_one({"authUserId": auth_user_id}):
        raise HTTPException(status_code=409, detail="User profile already exists.")

    # 2. Get the user's email from Clerk using the Clerk SDK
    try:
        api_client = clerk_client.ApiClient(clerk_client.configuration)
        users = users_api.UsersApi(api_client)
        clerk_user = users.get_user(user_id=auth_user_id)
        user_email = clerk_user.email_addresses[0].email_address if clerk_user.email_addresses else ""
    except Exception as e:
        print(f"Error fetching user from Clerk: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch user details from authentication provider.")

    # 3. Create the user document for MongoDB
    user_document = {
        "authUserId": auth_user_id,
        "email": user_email,
        "username": data.username.lower(),
        "name": data.name,
        "headline": data.headline,
        "profilePictureUrl": clerk_user.image_url or clerk_user.profile_image_url or "",
        "points": 0,
        "badges": [],
        "primaryGoal": data.primaryGoal,
        "preferredLanguages": data.preferredLanguages,
        "createdAt": datetime.utcnow(),
        "privateData": {
            "institutionName": data.institutionName,
            "location": data.location,
        },
        "tutorProfile": {"isTutor": False}
    }
    
    # 4. Insert the new user document
    try:
        result = users_collection.insert_one(user_document)
        if result.inserted_id:
            print(f"✅ Successfully created user profile for {data.username}")
            return JSONResponse(status_code=201, content={"message": "User profile created successfully"})
    except Exception as e:
        print(f"Database insertion error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while creating the user profile.")

    raise HTTPException(status_code=500, detail="An unexpected error occurred.")