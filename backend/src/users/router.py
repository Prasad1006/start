# backend/src/users/router.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from pydantic import BaseModel

# --- Import security dependency and service functions ---
# '..' goes up one level from 'users' to 'src', then into 'core'
from ..core.security import get_current_user
# '.' means import from the same 'users' module/directory
from . import service as user_service 

# Create a new router for this module.
# All endpoints defined here will be prefixed with /api/users
router = APIRouter(
    prefix="/api/users",
    tags=["Users & Profiles"] # This tag groups the endpoints in the auto-generated API docs
)

# --- Pydantic Models for Data Validation ---
# This defines the expected structure for the profile update request body.
class ProfileUpdate(BaseModel):
    headline: str
    primaryGoal: str
    preferredLanguages: List[str]

# --- API Endpoints ---

@router.get(
    "/profile", 
    summary="Get current logged-in user's full profile",
    description="Fetches the complete profile document from the database for the authenticated user."
)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    An endpoint to get the full profile of the user making the request.
    The user is identified by the JWT token.
    """
    user_id = current_user.get("sub")
    
    # Delegate the database logic to the service layer
    profile = await user_service.get_user_profile_by_id(user_id)
    
    if not profile:
        raise HTTPException(
            status_code=404, 
            detail="User profile not found in our database. Please complete onboarding."
        )
    return profile

@router.put(
    "/profile",
    summary="Update current user's profile",
    description="Allows a user to update their headline, primary goal, and preferred languages."
)
async def update_my_profile(profile_data: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    """
    An endpoint for users to update their own editable profile details.
    """
    user_id = current_user.get("sub")
    
    # Convert the Pydantic model to a dictionary to pass to the service layer
    update_data_dict = profile_data.dict()

    # Delegate the update logic to the service layer
    updated_user_count = await user_service.update_user_profile(user_id, update_data_dict)
    
    if updated_user_count == 0:
        raise HTTPException(
            status_code=404, 
            detail="Could not find user profile to update."
        )
        
    return {"message": "Profile updated successfully"}

@router.get(
    "/onboarding-status",
    summary="Check if the current user has completed onboarding",
    description="A simple gatekeeper endpoint to check for a user's existence in our database."
)
async def get_onboarding_status(current_user: dict = Depends(get_current_user)):
    """
    This endpoint is used by the frontend gatekeeper to determine if a user
    should be redirected to the onboarding flow or the dashboard.
    """
    user_id = current_user.get("sub")
    is_onboarded = await user_service.check_if_user_exists(user_id)
    
    if is_onboarded:
        return {"status": "completed"}
    else:
        return {"status": "pending"}

# Note: The /api/dashboard and /api/users/onboard endpoints are in their own
# respective modules (e.g., dashboard/router.py and auth/router.py) in a larger app.
# For our V1.0, keeping them here is fine, but this structure allows for future refactoring.