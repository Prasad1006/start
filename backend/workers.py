# backend/workers.py (FINAL, ROBUST VERSION)
import os
import sys
import json
import google.generativeai as genai
from fastapi import APIRouter, Request, HTTPException, status
from .database import roadmaps_collection, users_collection
from datetime import datetime

# Configure the router for worker endpoints
router = APIRouter()

@router.post("/api/workers/generate-roadmap", status_code=status.HTTP_202_ACCEPTED)
async def process_roadmap_generation(request: Request):
    """
    Worker endpoint to generate a learning roadmap using the Gemini API.
    Triggered by a message from the QStash queue.
    """
    if not roadmaps_collection or not users_collection:
        raise HTTPException(status_code=503, detail="Database service not available to worker.")

    # --- Robust Initialization inside the function ---
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("!!! FATAL WORKER ERROR: GEMINI_API_KEY environment variable is NOT SET.", file=sys.stderr)
        raise HTTPException(status_code=500, detail="AI service is not configured on the server.")

    try:
        # Initialize the client just-in-time
        genai.configure(api_key=gemini_api_key)

        body = await request.json()
        user_id = body.get("userId")
        skill_name = body.get("skill")

        if not user_id or not skill_name:
            raise HTTPException(status_code=400, detail="Missing userId or skill in job payload.")

        prompt = f"""
        Act as an expert curriculum designer. Your task is to create a detailed, structured, 8-week learning roadmap for the skill: "{skill_name}".
        The output MUST be a valid JSON object. Do not include any text or markdown formatting before or after the JSON.
        The JSON object should have a single key "weeklyPlan" which is an array of objects.
        Each object in the array represents a week and must have the following keys:
        - "week": (Number) The week number, from 1 to 8.
        - "topic": (String) A concise, clear title for the week's topic.
        - "description": (String) A 2-3 sentence summary of what the learner will cover and achieve this week.
        - "status": (String) The initial status, which must be "PENDING".

        Now, generate the full 8-week plan for "{skill_name}".
        """

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async(prompt)
        
        cleaned_response = response.text.replace("```json", "").replace("```", "").strip()
        roadmap_data = json.loads(cleaned_response)

        roadmap_document = {
            "userId": user_id,
            "skill": skill_name,
            "skill_slug": skill_name.lower().replace(" ", "-").replace("/", "-").replace(".", ""),
            "weeklyPlan": roadmap_data.get("weeklyPlan", []),
            "createdAt": datetime.utcnow()
        }
        roadmaps_collection.insert_one(roadmap_document)

        print(f"✅ Successfully generated roadmap for user {user_id} and skill {skill_name}", file=sys.stderr)
        return {"status": "success", "message": "Roadmap generated and saved."}

    except json.JSONDecodeError as e:
        print(f"!!! WORKER ERROR: Failed to decode JSON from Gemini API. Response was: {response.text}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="Failed to parse AI response.")
    except Exception as e:
        print(f"!!! WORKER ERROR: An unexpected error occurred: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"An internal worker error occurred: {e}")