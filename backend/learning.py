# backend/learning.py (FINAL SIMPLIFIED VERSION)
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from .auth import get_current_user
from .database import get_db_dependency
from datetime import datetime

router = APIRouter()

@router.post("/api/roadmaps/request", status_code=status.HTTP_202_ACCEPTED)
async def request_roadmap_generation(
    data: dict, 
    db: Database = Depends(get_db_dependency),
    current_user: dict = Depends(get_current_user)
):
    """
    Creates a request document in the database, which will be picked up 
    by the cron job worker. This is fast and reliable.
    """
    skill_name = data.get("skill")
    if not skill_name:
        raise HTTPException(status_code=400, detail="Skill name is required.")

    user_id = current_user.get("sub")

    # Check if a request for this skill already exists and is not failed
    existing_request = db.roadmap_requests.find_one({
        "userId": user_id,
        "skill": skill_name,
        "status": {"$in": ["PENDING", "PROCESSING"]}
    })
    if existing_request:
        return {"message": "A roadmap for this skill is already being generated."}

    # Create the new request document
    request_doc = {
        "userId": user_id,
        "skill": skill_name,
        "status": "PENDING",
        "createdAt": datetime.utcnow()
    }
    db.roadmap_requests.insert_one(request_doc)

    return {"message": "Your roadmap request has been received and will be processed shortly."}

# The GET endpoint for retrieving a completed roadmap does not change
@router.get("/api/roadmaps/{skill_slug}")
async def get_roadmap_by_skill(
    skill_slug: str, 
    db: Database = Depends(get_db_dependency), 
    current_user: dict = Depends(get_current_user)
):
    roadmap = db.roadmaps.find_one({"userId": current_user.get("sub"), "skill_slug": skill_slug})
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found. It may still be generating or has not been requested.")
    roadmap["_id"] = str(roadmap["_id"])
    return roadmap