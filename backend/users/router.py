# backend/users/router.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel

# The import path is now simple because 'core' and 'users' are sibling directories.
from core.security import get_current_user
from users import service as user_service 

router = APIRouter(
    prefix="/api/users",
    tags=["Users & Profiles"]
)

# --- Pydantic Models for Data Validation ---
class OnboardingData(BaseModel):
    # This model remains correct from previous versions
    username: str; headline: str; primaryGoal: str; preferredLanguages: List[str]; stream: str; branch: str
    selectedDomains: List[str]; skillsToLearn: List[str] = []; skillsToTeach: List[str] = []

# --- API Endpoints ---
# The logic inside these endpoints does not need to change from the last complete version.
# The only change required was the import statements at the top.

@router.post("/onboard", status_code=status.HTTP_201_CREATED)
async def onboard_user_endpoint(data: OnboardingData, current_user: dict = Depends(get_current_user)):
    return await user_service.create_new_user(data, current_user)

@router.get("/profile")
async def get_my_profile_endpoint(current_user: dict = Depends(get_current_user)):
    profile = await user_service.get_user_profile_by_id(current_user.get("sub"))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return profile

@router.get("/onboarding-status")
async def get_onboarding_status_endpoint(current_user: dict = Depends(get_current_user)):
    is_onboarded = await user_service.check_if_user_exists(current_user.get("sub"))
    return {"status": "completed" if is_onboarded else "pending"}

@router.get("/dashboard") # Assuming dashboard logic is here for now
async def get_dashboard_data_endpoint(current_user: dict = Depends(get_current_user)):
    dashboard_data = await user_service.get_dashboard_data(current_user.get("sub"))
    if not dashboard_data:
        raise HTTPException(status_code=404, detail="Could not fetch dashboard data.")
    return dashboard_data