# backend/src/users/service.py

from ..core.database import users_collection # Assumes database.py is in the core folder
from datetime import datetime

async def get_user_profile_by_id(user_id: str):
    """Fetches a user profile from the database by their unique user ID."""
    if users_collection is None: return None
    
    user_profile = users_collection.find_one({"userId": user_id})
    if user_profile:
        user_profile["_id"] = str(user_profile["_id"])
    return user_profile

async def check_if_user_exists(user_id: str) -> bool:
    """Checks if a user exists by their ID."""
    if users_collection is None: return False
    return users_collection.count_documents({"userId": user_id}) > 0

async def check_if_username_exists(username: str) -> bool:
    """Checks if a username is already taken."""
    if users_collection is None: return False
    return users_collection.count_documents({"username": username}) > 0

async def create_user_profile(user_id: str, email: str, clerk_user: dict, onboarding_data):
    """Creates a new user document in the database."""
    if users_collection is None:
        raise Exception("Database service is not available.")

    user_document = {
        "userId": user_id,
        "username": onboarding_data.username,
        "email": email,
        "name": clerk_user.get("name") or f"{clerk_user.get('firstName', '')} {clerk_user.get('lastName', '')}".strip(),
        "headline": onboarding_data.headline,
        "profilePictureUrl": clerk_user.get("imageUrl", ""),
        "points": 100,
        "badges": ["The Trailblazer"],
        "primaryGoal": onboarding_data.primaryGoal,
        "preferredLanguages": onboarding_data.preferredLanguages,
        "createdAt": datetime.utcnow(),
        "learningProfile": {
            "stream": onboarding_data.stream,
            "branch": onboarding_data.branch,
            "domains": onboarding_data.selectedDomains,
            "skillsToLearn": onboarding_data.skillsToLearn
        },
        "tutorProfile": {
            "isTutor": len(onboarding_data.skillsToTeach) > 0,
            "teachableModules": []
        }
    }
    users_collection.insert_one(user_document)
    return True