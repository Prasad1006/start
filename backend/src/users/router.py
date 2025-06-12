# backend/src/users/router.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel

# ** THIS IS THE CRITICAL FIX **
# '..' goes up one directory from 'users' to 'src', then into 'core'.
from core.security import get_current_user
# '.' means import from a file in the same 'users' directory.
from users import service as user_service 

# Create a new router for this module
router = APIRouter(
    prefix="/api/users",
    tags=["Users & Profiles"]
)

# --- Pydantic Models for Data Validation ---
class OnboardingData(BaseModel):
    username: str
    headline: str
    primaryGoal: str
    preferredLanguages: List[str]
    stream: str
    branch: str
    selectedDomains: List[str]
    skillsToLearn: List[str] = []
    skillsToTeach: List[str] = []

# --- API Endpoints ---

@router.post("/onboard", status_code=status.HTTP_201_CREATED)
async def onboard_user_endpoint(data: OnboardingData, current_user: dict = Depends(get_current_user)):
    """
    Handles the final step of user onboarding.
    """
    user_id = current_user.get("sub")
    email = current_user.get("email_addresses", [None])[0]
    
    # Check for duplicates first
    is_existing = await user_service.check_if_user_exists(user_id)
    if is_existing:
        return {"message": "User already has a profile."}
        
    is_username_taken = await user_service.check_if_username_exists(data.username)
    if is_username_taken:
        raise HTTPException(status_code=400, detail="Username is already taken.")
        
    # Delegate the creation logic to the service layer
    await user_service.create_user_profile(user_id, email, current_user, data)
    return {"message": "Onboarding successful!"}

@router.get("/profile")
async def get_my_profile_endpoint(current_user: dict = Depends(get_current_user)):
    """
    Fetches the profile for the currently logged-in user.
    """
    user_id = current_user.get("sub")
    profile = await user_service.get_user_profile_by_id(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return profile