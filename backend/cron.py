# backend/cron.py (NEW FILE)
import os
import sys
import json
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pymongo.database import Database
from .database import get_db_dependency
from datetime import datetime

router = APIRouter()
CRON_SECRET = os.getenv("CRON_SECRET")

@router.post("/api/cron/process-roadmaps")
async def process_pending_roadmaps(
    x_cron_secret: str = Header(None), 
    db: Database = Depends(get_db_dependency)
):
    """
    This endpoint is called by a Vercel Cron Job every minute.
    It processes one pending roadmap request from the database.
    """
    print("--- Cron job triggered. ---", file=sys.stderr)
    
    # 1. Secure the endpoint
    if not CRON_SECRET or x_cron_secret != CRON_SECRET:
        print("!!! CRON-ERROR: Unauthorized access attempt.", file=sys.stderr)
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 2. Find ONE pending request and update it to "PROCESSING" atomically.
    #    This prevents multiple workers from grabbing the same job.
    pending_request = db.roadmap_requests.find_one_and_update(
        {"status": "PENDING"},
        {"$set": {"status": "PROCESSING", "processedAt": datetime.utcnow()}}
    )

    if not pending_request:
        print("No pending roadmap requests found. Exiting.", file=sys.stderr)
        return {"status": "no_pending_requests"}
        
    print(f"Processing request for user {pending_request['userId']} and skill {pending_request['skill']}", file=sys.stderr)

    # 3. Get the Gemini API Key
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("!!! CRON-ERROR: GEMINI_API_KEY env var not set.", file=sys.stderr)
        db.roadmap_requests.update_one({"_id": pending_request["_id"]}, {"$set": {"status": "FAILED", "error": "AI service not configured"}})
        raise HTTPException(status_code=500, detail="AI service not configured.")

    try:
        # 4. Generate the Roadmap (The heavy lifting)
        genai.configure(api_key=gemini_api_key)
        prompt = f"""... Generate 8-week plan for "{pending_request['skill']}" ...""" # Use the full prompt from before
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async(prompt)
        roadmap_data = json.loads(response.text.replace("```json", "").replace("```", "").strip())

        # 5. Save the result to the main 'roadmaps' collection
        roadmap_document = {
            "userId": pending_request['userId'],
            "skill": pending_request['skill'],
            "skill_slug": pending_request['skill'].lower().replace(" ", "-").replace("/", "-").replace(".", ""),
            "weeklyPlan": roadmap_data.get("weeklyPlan", []),
            "createdAt": datetime.utcnow()
        }
        db.roadmaps.insert_one(roadmap_document)

        # 6. Mark the original request as completed
        db.roadmap_requests.update_one({"_id": pending_request["_id"]}, {"$set": {"status": "COMPLETED"}})
        
        print(f"✅ Successfully processed request for skill: {pending_request['skill']}", file=sys.stderr)
        return {"status": "success", "processed_skill": pending_request['skill']}

    except Exception as e:
        error_message = f"Failed to process roadmap: {e}"
        print(f"!!! CRON-ERROR: {error_message}", file=sys.stderr)
        db.roadmap_requests.update_one({"_id": pending_request["_id"]}, {"$set": {"status": "FAILED", "error": str(e)}})
        raise HTTPException(status_code=500, detail=error_message)