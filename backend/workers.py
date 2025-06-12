# backend/workers.py (REVISED FOR NEW SECURITY)
import os
import sys
import json
import google.generativeai as genai
from fastapi import APIRouter, Request, HTTPException, status, Header
from .database import roadmaps_collection
from datetime import datetime

router = APIRouter()

# Get the secret key from the environment
WORKER_SECRET_KEY = os.getenv("WORKER_SECRET_KEY")

@router.post("/api/workers/generate-roadmap", status_code=status.HTTP_202_ACCEPTED)
async def process_roadmap_generation(
    request: Request,
    x_worker_secret: str = Header(None) # Expect the key in a header
):
    """
    Worker endpoint to generate a learning roadmap using the Gemini API.
    Now secured with a secret header instead of QStash.
    """
    # --- NEW SECURITY CHECK ---
    if not WORKER_SECRET_KEY or x_worker_secret != WORKER_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized worker access.")

    # ... (The rest of this function remains exactly the same as before)
    if not roadmaps_collection:
        raise HTTPException(status_code=503, detail="Database service not available to worker.")

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="AI service is not configured.")

    try:
        genai.configure(api_key=gemini_api_key)
        body = await request.json()
        user_id, skill_name = body.get("userId"), body.get("skill")
        if not user_id or not skill_name:
            raise HTTPException(status_code=400, detail="Missing data in payload.")
        
        prompt = f"""...""" # Your AI prompt remains the same

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async(prompt)
        
        cleaned_response = response.text.replace("```json", "").replace("```", "").strip()
        roadmap_data = json.loads(cleaned_response)
        
        roadmap_document = {
            "userId": user_id, "skill": skill_name,
            "skill_slug": skill_name.lower().replace(" ", "-").replace("/", "-").replace(".", ""),
            "weeklyPlan": roadmap_data.get("weeklyPlan", []), "createdAt": datetime.utcnow()
        }
        roadmaps_collection.insert_one(roadmap_document)
        
        return {"status": "success"}

    except Exception as e:
        print(f"!!! WORKER ERROR: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="An internal worker error occurred.")