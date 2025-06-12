# backend/users/service.py

from datetime import datetime
# The import path is now simple.
from core.database import users_collection, roadmaps_collection

async def check_if_user_exists(user_id: str) -> bool:
    if users_collection is None: return False
    return users_collection.count_documents({"userId": user_id}) > 0

async def check_if_username_exists(username: str) -> bool:
    if users_collection is None: return False
    return users_collection.count_documents({"username": username}) > 0

async def create_new_user(data, clerk_user):
    from fastapi.responses import JSONResponse

    if users_collection is None:
        return JSONResponse(status_code=503, content={"error": "Database service is not available."})

    user_id = clerk_user.get("sub")
    if await check_if_user_exists(user_id):
        return JSONResponse(status_code=200, content={"message": "User already has a profile."})
    if await check_if_username_exists(data.username):
        return JSONResponse(status_code=400, content={"error": "Username is already taken."})
    
    user_document = {
        "userId": user_id,
        "username": data.username,
        "email": clerk_user.get("email_addresses", [None])[0],
        "name": clerk_user.get("name") or f"{clerk_user.get('firstName', '')} {clerk_user.get('lastName', '')}".strip(),
        "headline": data.headline,
        "profilePictureUrl": clerk_user.get("imageUrl", ""),
        "points": 100,
        "badges": ["The Trailblazer"],
        "primaryGoal": data.primaryGoal,
        "preferredLanguages": data.preferredLanguages,
        "createdAt": datetime.utcnow(),
        "learningProfile": {
            "stream": data.stream,
            "branch": data.branch,
            "domains": data.selectedDomains,
            "skillsToLearn": data.skillsToLearn
        },
        "tutorProfile": {
            "isTutor": len(data.skillsToTeach) > 0,
            "teachableModules": []
        }
    }
    users_collection.insert_one(user_document)
    return {"message": "Onboarding successful!"}


async def get_user_profile_by_id(user_id: str):
    if users_collection is None: return None
    user_profile = users_collection.find_one({"userId": user_id})
    if user_profile:
        user_profile["_id"] = str(user_profile["_id"])
    return user_profile

async def get_dashboard_data(user_id: str):
    user_profile = await get_user_profile_by_id(user_id)
    if not user_profile: return None
    return {
        "name": user_profile.get("name", ""),
        "points": user_profile.get("points", 0),
        "isTutor": user_profile.get("tutorProfile", {}).get("isTutor", False),
        "learningTracks": [] # Placeholder
    }