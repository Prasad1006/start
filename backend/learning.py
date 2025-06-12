# backend/learning.py
import os
import sys
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from .auth import get_current_user
from .database import roadmaps_collection

print(f"In {__file__}, WORKER_SECRET_KEY is set: {os.getenv('WORKER_SECRET_KEY') is not None}", file=sys.stderr)

router = APIRouter()
WORKER_SECRET_KEY = os.getenv("WORKER_SECRET_KEY")

async def trigger_worker(url: str, payload: dict, headers: dict):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload, headers=headers, timeout=10)
            print(f"✅ Successfully dispatched job to worker: {url}", file=sys.stderr)
        except httpx.RequestError as e:
            print(f"!!! FAILED TO DISPATCH JOB TO WORKER: {e}", file=sys.stderr)

@router.post("/api/roadmaps", status_code=202)
async def request_roadmap_generation(
    request: Request,
    data: dict,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    skill_name = data.get("skill")
    user_id = current_user.get("sub")

    if not skill_name:
        raise HTTPException(status_code=400, detail="Skill name is required.")
    if not WORKER_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Worker service is not configured.")

    base_url = str(request.base_url).rstrip("/")
    worker_url = f"{base_url}/api/workers/generate-roadmap"

    payload = {"userId": user_id, "skill": skill_name}
    headers = {"x-worker-secret": WORKER_SECRET_KEY}

    background_tasks.add_task(trigger_worker, worker_url, payload, headers)
    return {"message": "Roadmap generation has been successfully scheduled."}

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
