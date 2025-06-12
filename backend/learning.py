import os, sys, httpx
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pymongo.database import Database
from .auth import get_current_user
from .database import get_db_dependency

router = APIRouter()
WORKER_SECRET_KEY = os.getenv("WORKER_SECRET_KEY")

async def trigger_worker(url: str, payload: dict, headers: dict):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload, headers=headers, timeout=5)
        except httpx.RequestError as e:
            print(f"!!! FAILED TO DISPATCH JOB TO WORKER: {e}", file=sys.stderr)

@router.post("/api/roadmaps", status_code=status.HTTP_202_ACCEPTED)
async def request_roadmap_generation(data: dict, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    skill_name = data.get("skill")
    if not skill_name: raise HTTPException(status_code=400, detail="Skill name is required.")
    if not WORKER_SECRET_KEY: raise HTTPException(status_code=503, detail="Worker service not configured.")
    base_url = os.getenv("VERCEL_URL", "http://localhost:8000")
    if not base_url.startswith("http"): base_url = "https://" + base_url
    worker_url = f"{base_url}/api/workers/generate-roadmap"
    payload = {"userId": current_user.get("sub"), "skill": skill_name}
    headers = {"x-worker-secret": WORKER_SECRET_KEY}
    background_tasks.add_task(trigger_worker, worker_url, payload, headers)
    return {"message": "Roadmap generation has been successfully scheduled."}

@router.get("/api/roadmaps/{skill_slug}")
async def get_roadmap_by_skill(skill_slug: str, db: Database = Depends(get_db_dependency), current_user: dict = Depends(get_current_user)):
    roadmap = db.roadmaps.find_one({"userId": current_user.get("sub"), "skill_slug": skill_slug})
    if not roadmap: raise HTTPException(status_code=404, detail="Roadmap not found.")
    roadmap["_id"] = str(roadmap["_id"])
    return roadmap