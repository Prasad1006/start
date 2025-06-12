# backend/learning.py (FINAL, CORRECT URL HANDLING)
import os
import sys
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from .auth import get_current_user 

router = APIRouter()

# --- Use the static secret for maximum reliability ---
STATIC_WORKER_SECRET = "a-very-secret-and-hard-to-guess-string-12345"

async def trigger_worker(url: str, payload: dict, headers: dict):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload, headers=headers, timeout=10)
            print(f"✅ Dispatched job to worker: {url}", file=sys.stderr)
        except httpx.RequestError as e:
            print(f"!!! FAILED TO DISPATCH JOB TO WORKER: {e}", file=sys.stderr)

@router.post("/api/roadmaps", status_code=202)
async def request_roadmap_generation(
    data: dict,
    request: Request, # <-- Add the request object to get the host URL
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    skill_name = data.get("skill")
    user_id = current_user.get("sub")
    if not skill_name: raise HTTPException(status_code=400, detail="Skill name is required.")
    
    # --- THIS IS THE CORRECT, ROBUST WAY TO GET THE URL ---
    # It constructs the URL based on the *actual request* the user made.
    # This works both locally and on Vercel without needing VERCEL_URL.
    scheme = request.url.scheme
    host = request.url.netloc
    base_url = f"{scheme}://{host}"
    
    worker_url = f"{base_url}/api/workers/generate-roadmap"
    
    payload = {"userId": user_id, "skill": skill_name}
    headers = {"x-worker-secret": STATIC_WORKER_SECRET}
    
    background_tasks.add_task(trigger_worker, worker_url, payload, headers)

    return {"message": "Roadmap generation has been successfully scheduled."}


@router.get("/api/roadmaps/{skill_slug}")
async def get_roadmap_by_skill(skill_slug: str, current_user: dict = Depends(get_current_user)):
    from .database import roadmaps_collection
    if roadmaps_collection is None: raise HTTPException(status_code=503, detail="Database service unavailable.")
    user_id = current_user.get("sub")
    roadmap = roadmaps_collection.find_one({"userId": user_id, "skill_slug": skill_slug})
    if not roadmap: raise HTTPException(status_code=404, detail="Roadmap not found.")
    roadmap["_id"] = str(roadmap["_id"])
    return roadmap