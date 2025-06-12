# backend/workers.py
import os, sys, json, google.generativeai as genai
from fastapi import APIRouter, Request, HTTPException, Header
from datetime import datetime
from urllib.parse import quote
from .database import roadmaps_collection

router = APIRouter()
WORKER_SECRET_KEY = os.getenv("WORKER_SECRET_KEY")

@router.post("/api/workers/generate-roadmap", status_code=202)
async def process_roadmap_generation(request: Request, x_worker_secret: str = Header(None)):
    if not WORKER_SECRET_KEY or x_worker_secret != WORKER_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized worker access.")
    if not roadmaps_collection:
        raise HTTPException(status_code=503, detail="DB service not available to worker.")

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="AI service not configured.")
        
    try:
        genai.configure(api_key=gemini_api_key)
        body = await request.json()
        user_id, skill_name = body.get("userId"), body.get("skill")
        # ... (rest of your AI generation logic from before) ...
    except Exception as e:
        print(f"!!! WORKER ERROR: {e}", file=sys.stderr)
        # We don't raise an exception here because the job has already been "accepted".
        # In a production app, you would log this to a monitoring service.