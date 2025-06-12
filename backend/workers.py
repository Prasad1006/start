import os, sys, json, google.generativeai as genai
from fastapi import APIRouter, Request, HTTPException, status, Header, Depends
from pymongo.database import Database
from .database import get_db_dependency
from datetime import datetime

router = APIRouter()
WORKER_SECRET_KEY = os.getenv("WORKER_SECRET_KEY")

@router.post("/api/workers/generate-roadmap", status_code=status.HTTP_202_ACCEPTED)
async def process_roadmap_generation(req: Request, x_worker_secret: str = Header(None), db: Database = Depends(get_db_dependency)):
    if not WORKER_SECRET_KEY or x_worker_secret != WORKER_SECRET_KEY: raise HTTPException(status_code=401, detail="Unauthorized worker access.")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key: raise HTTPException(status_code=500, detail="AI service is not configured.")
    try:
        genai.configure(api_key=gemini_api_key)
        body = await req.json()
        user_id, skill_name = body.get("userId"), body.get("skill")
        if not user_id or not skill_name: raise HTTPException(status_code=400, detail="Missing data in payload.")
        prompt = f"""Act as an expert curriculum designer... for "{skill_name}"...""" # Your prompt
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async(prompt)
        roadmap_data = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        doc = { "userId": user_id, "skill": skill_name, "skill_slug": skill_name.lower().replace(" ", "-").replace("/", "-").replace(".", ""), "weeklyPlan": roadmap_data.get("weeklyPlan", []), "createdAt": datetime.utcnow() }
        db.roadmaps.insert_one(doc)
        return {"status": "success"}
    except Exception as e:
        print(f"!!! WORKER ERROR: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="An internal worker error occurred.")