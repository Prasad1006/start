# backend/learning.py (FINAL VERSION - NO QSTASH)
import os
import sys
import asyncio
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from .database import roadmaps_collection
from .auth import get_current_user 

# Configure the router
router = APIRouter()
WORKER_SECRET_KEY = os.getenv("WORKER_SECRET_KEY")

async def trigger_worker(url: str, payload: dict, headers: dict):
    """A helper function to make a non-blocking HTTP request."""
    async with httpx.AsyncClient() as client:
        try:
            # We send the request but don't wait for a response, simulating a queue.
            await client.post(url, json=payload, headers=headers, timeout=5)
            print(f"Successfully dispatched job to worker: {url}", file=sys.stderr)
        except httpx.RequestError as e:
            print(f"!!! FAILED TO DISPATCH JOB TO WORKER: {e}", file=sys.stderr)

@router.post("/api/roadmaps", status_code=status.HTTP_202_ACCEPTED)
async def request_roadmap_generation(
    data: dict,
    background_tasks: BackgroundTasks, # FastAPI's built-in way to run tasks
    current_user: dict = Depends(get_current_user)
):
    """
    Receives a request to generate a roadmap. It uses FastAPI's BackgroundTasks
    to call the worker endpoint without blocking.
    """
    skill_name = data.get("skill")
    user_id = current_user.get("sub")

    if not skill_name:
        raise HTTPException(status_code=400, detail="Skill name is required.")

    if not WORKER_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Worker service is not configured.")

    # We need the full URL of our own application to call the worker.
    # On Vercel, this is automatically set.
    base_url = os.getenv("VERCEL_URL", "http://localhost:8000")
    if not base_url.startswith("http"):
        base_url = "https://" + base_url

    worker_url = f"{base_url}/api/workers/generate-roadmap"
    
    payload = {"userId": user_id, "skill": skill_name}
    headers = {"x-worker-secret": WORKER_SECRET_KEY}
    
    # Use FastAPI's robust background task manager.
    background_tasks.add_task(trigger_worker, worker_url, payload, headers)

    return {"message": "Roadmap generation has been successfully scheduled."}


# This endpoint remains exactly the same
@router.get("/api/roadmaps/{skill_slug}")
async def get_roadmap_by_skill(skill_slug: str, current_user: dict = Depends(get_current_user)):
    if roadmaps_collection is None:
        raise HTTPException(status_code=503, detail="Database service unavailable.")
    user_id = current_user.get("sub")
    roadmap = roadmaps_collection.find_one({"userId": user_id, "skill_slug": skill_slug})
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found.")
    roadmap["_id"] = str(roadmap["_id"])
    return roadmap