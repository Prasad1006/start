# backend/learning.py (THE FINAL, DOCUMENTATION-ALIGNED VERSION)
import os
import sys
from fastapi import APIRouter, Depends, HTTPException, status
# This is the correct, documented import path for the main class.
from qstash import QStash 
from .database import roadmaps_collection
from .auth import get_current_user 

# Configure the router for our learning-related endpoints
router = APIRouter()

@router.post("/api/roadmaps", status_code=status.HTTP_202_ACCEPTED)
async def request_roadmap_generation(
    data: dict, 
    current_user: dict = Depends(get_current_user)
):
    """
    Receives a request to generate a roadmap. This endpoint queues a job for a 
    background worker and returns immediately, preventing timeouts.
    """
    skill_name = data.get("skill")
    user_id = current_user.get("sub")

    if not skill_name:
        raise HTTPException(status_code=400, detail="Skill name is required.")

    # --- Robust Initialization inside the endpoint (this architecture is correct) ---
    qstash_token = os.getenv("QSTASH_TOKEN")
    qstash_url = os.getenv("QSTASH_URL")

    if not qstash_token or not qstash_url:
         raise HTTPException(
             status_code=503, 
             detail="Queue service is not configured correctly on the server. Please contact support."
         )

    try:
        # This is the correct, documented way to initialize the client.
        client = QStash({"token": qstash_token})

        # The publish_json method is correct for this client object.
        client.publish_json({
            "url": f"{qstash_url}/api/workers/generate-roadmap",
            "body": {"userId": user_id, "skill": skill_name}
        })
        
        return {"message": "Roadmap generation has been queued successfully."}

    except Exception as e:
        print(f"!!! FAILED TO QUEUE ROADMAP JOB: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while queueing the job.")


# This endpoint does not use QStash and does not need to change.
@router.get("/api/roadmaps/{skill_slug}")
async def get_roadmap_by_skill(skill_slug: str, current_user: dict = Depends(get_current_user)):
    """
    Fetches a single, generated roadmap for the logged-in user and a specific skill.
    """
    if roadmaps_collection is None:
        raise HTTPException(status_code=503, detail="Database service unavailable.")

    user_id = current_user.get("sub")
    
    roadmap = roadmaps_collection.find_one({"userId": user_id, "skill_slug": skill_slug})
    
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found. It may still be generating or has not been requested.")

    roadmap["_id"] = str(roadmap["_id"])
    
    return roadmap