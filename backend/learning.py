import os
import sys
import requests
from fastapi import APIRouter, Depends, HTTPException, status
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

    # Get environment variables
    qstash_token = os.getenv("QSTASH_TOKEN")
    forward_url = os.getenv("QSTASH_FORWARD_URL")  # E.g., https://yourdomain.com/api/workers/generate-roadmap

    if not qstash_token or not forward_url:
        raise HTTPException(
            status_code=503,
            detail="Queue service is not configured correctly on the server. Please contact support."
        )

    try:
        headers = {
            "Authorization": f"Bearer {qstash_token}",
            "Upstash-Forward-To": forward_url,
            "Content-Type": "application/json"
        }

        payload = {
            "userId": user_id,
            "skill": skill_name
        }

        response = requests.post("https://qstash.upstash.io/v1/publish", headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Failed to publish job: {response.text}")

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
