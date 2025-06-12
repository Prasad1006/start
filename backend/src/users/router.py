# backend/src/users/router.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from pydantic import BaseModel
from . import service as user_service # Import the logic from the service file
from ..core.security import get_current_user # Assume security logic is in core

router = APIRouter(prefix="/api/users", tags=["Users"])

# --- Pydantic Models for Data Validation ---
class ProfileUpdate(BaseModel):
    headline: str
    primaryGoal: str
    preferredLanguages: List[str]

# --- API Endpoints ---
@router.get("/profile", summary="Get current user's full profile")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("sub")
    profile = await user_service.get_user_profile_by_id(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return profile

@router.put("/profile", summary="Update current user's profile")
async def update_my_profile(profile_data: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("sub")
    updated_user = await user_service.update_user_profile(user_id, profile_data.dict())
    if not updated_user:
        raise HTTPException(status_code=404, detail="Could not update profile.")
    return {"message": "Profile updated successfully", "user": updated_user}

# ... Other user-related endpoints like /dashboard can also go here ...