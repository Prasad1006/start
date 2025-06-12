# backend/workers.py
import os
import sys
import json
import google.generativeai as genai
from fastapi import APIRouter, Request, HTTPException, status, Header
from datetime import datetime
from urllib.parse import quote
from .database import roadmaps_collection

print(f"In {__file__}, WORKER_SECRET_KEY is set: {os.getenv('WORKER_SECRET_KEY') is not None}", file=sys.stderr)

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
        if not user_id or not skill_name:
            raise HTTPException(status_code=400, detail="Missing data in payload.")

        prompt = f"""Act as an expert curriculum designer. Your task is to create a detailed, structured, 8-week learning roadmap for the skill: \"{skill_name}\".\nThe output MUST be a valid JSON array (not an object). Do not include any text or markdown formatting.\nEach object in the array must have keys \"week\", \"topic\", \"description\", and \"status\" (initially \"PENDING\")."""

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async(prompt)

        try:
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            roadmap_data = json.loads(raw_text)
            weekly_plan = roadmap_data if isinstance(roadmap_data, list) else roadmap_data.get("weeklyPlan", [])
        except Exception as parse_error:
            print("❌ Gemini raw output:", response.text, file=sys.stderr)
            raise HTTPException(status_code=500, detail="Failed to parse Gemini AI output.")

        safe_skill_slug = quote(skill_name.lower().replace(" ", "-"), safe='')
        doc = {
            "userId": user_id,
            "skill": skill_name,
            "skill_slug": safe_skill_slug,
            "weeklyPlan": weekly_plan,
            "createdAt": datetime.utcnow()
        }

        roadmaps_collection.insert_one(doc)
        return {"status": "success"}

    except Exception as e:
        print(f"!!! WORKER ERROR: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="Internal worker error.")
