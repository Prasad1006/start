# backend/learning.py (FINAL, ROBUST VERSION)
import os
import sys
from fastapi import APIRouter, Depends, HTTPException, status
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
    Receives a request to generate a roadmap. It queues a job for a 
    background worker and returns immediately.
    """
    skill_name = data.get("skill")
    user_id = current_user.get("sub")

    if not skill_name:
        raise HTTPException(status_code=400, detail="Skill name is required.")

    # --- Robust Initialization inside the endpoint ---
    qstash_token = os.getenv("QSTASH_TOKEN")
    qstash_url = os.getenv("QSTASH_URL")

    if not qstash_token or not qstash_url:
         raise HTTPException(
             status_code=503, 
             detail="Queue service is not configured on the server. Please contact support."
         )

    try:
        # Initialize the client just-in-time.
        client = QStash({"token": qstash_token})

        # Publish the job to the worker.
        client.publish_json({
            "url": f"{qstash_url}/api/workers/generate-roadmap",
            "body": {"userId": user_id, "skill": skill_name}
        })
        
        return {"message": "Roadmap generation has been queued successfully."}
    except Exception as e:
        print(f"!!! FAILED TO QUEUE ROADMAP JOB: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while queueing the job.")


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