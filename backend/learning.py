# backend/learning.py (FINAL CORRECTED VERSION)
import os
from fastapi import APIRouter, Depends, HTTPException, status
from qstash import client # <<< THE FINAL FIX: Import 'client' with a lowercase 'c'
from .database import roadmaps_collection
from .auth import get_current_user 

# Configure the router and QStash client
router = APIRouter()
QSTASH_URL = os.getenv("QSTASH_URL")
QSTASH_TOKEN = os.getenv("QSTASH_TOKEN")

# The library needs to be initialized outside the function
# so it can be reused across requests.
qstash_http_client = None # Renaming to be more descriptive
if QSTASH_TOKEN:
    qstash_http_client = client(QSTASH_TOKEN) # <<< THE FINAL FIX: Instantiate 'client' with a lowercase 'c'

# This endpoint is called by the user's "Generate" button.
@router.post("/api/roadmaps", status_code=status.HTTP_202_ACCEPTED)
async def request_roadmap_generation(
    data: dict, 
    current_user: dict = Depends(get_current_user)
):
    """
    Receives a request from the user to generate a learning roadmap.
    It creates a job and sends it to the QStash queue for background processing.
    """
    skill_name = data.get("skill")
    user_id = current_user.get("sub")

    if not skill_name:
        raise HTTPException(status_code=400, detail="Skill name is required.")

    if not qstash_http_client or not QSTASH_URL:
         raise HTTPException(status_code=500, detail="Queue service is not configured.")

    try:
        # The method call itself was correct
        qstash_http_client.publish_json({
            "url": f"{QSTASH_URL}/api/workers/generate-roadmap",
            "body": {"userId": user_id, "skill": skill_name}
        })
        return {"message": "Roadmap generation has been queued."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {e}")

# This endpoint is called by the new roadmap.html page.
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
        raise HTTPException(status_code=404, detail="Roadmap not found or not generated yet.")

    # Convert ObjectId to string for JSON serialization
    roadmap["_id"] = str(roadmap["_id"])
    return roadmap