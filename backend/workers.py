# backend/workers.py (new file)
import os
import sys
import json
import google.generativeai as genai
from fastapi import APIRouter, Request, HTTPException, status
from .database import roadmaps_collection, users_collection
from datetime import datetime

# Configure the router and Gemini API
router = APIRouter()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("!!! FATAL WORKER ERROR: GEMINI_API_KEY environment variable is NOT SET.", file=sys.stderr)

# This is the endpoint that Upstash QStash will call.
# It's a "webhook" for our background jobs.
@router.post("/api/workers/generate-roadmap", status_code=status.HTTP_202_ACCEPTED)
async def process_roadmap_generation(request: Request):
    """
    Worker endpoint to generate a learning roadmap using the Gemini API.
    Triggered by a message from the QStash queue.
    """
    if not roadmaps_collection or not users_collection:
        raise HTTPException(status_code=503, detail="Database service not available to worker.")
    
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured for worker.")

    try:
        # 1. Receive the job payload from QStash
        body = await request.json()
        user_id = body.get("userId")
        skill_name = body.get("skill")

        if not user_id or not skill_name:
            raise HTTPException(status_code=400, detail="Missing userId or skill in job payload.")

        # 2. Prepare the AI prompt
        prompt = f"""
        Act as an expert curriculum designer. Your task is to create a detailed, structured, 8-week learning roadmap for the skill: "{skill_name}".
        The output MUST be a valid JSON object. Do not include any text or markdown formatting before or after the JSON.
        The JSON object should have a single key "weeklyPlan" which is an array of objects.
        Each object in the array represents a week and must have the following keys:
        - "week": (Number) The week number, from 1 to 8.
        - "topic": (String) A concise, clear title for the week's topic.
        - "description": (String) A 2-3 sentence summary of what the learner will cover and achieve this week.
        - "status": (String) The initial status, which must be "PENDING".

        Example for "React.js":
        {{
          "weeklyPlan": [
            {{
              "week": 1,
              "topic": "Fundamentals: JSX, Components & Props",
              "description": "Understand the core concepts of React. Learn how to write UI with JSX, create functional components, and pass data using props.",
              "status": "PENDING"
            }}
          ]
        }}
        
        Now, generate the full 8-week plan for "{skill_name}".
        """

        # 3. Call the Gemini API
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async(prompt)
        
        # 4. Clean and parse the response
        # The API sometimes wraps the JSON in markdown, so we remove it.
        cleaned_response = response.text.replace("```json", "").replace("```", "").strip()
        roadmap_data = json.loads(cleaned_response)

        # 5. Save the generated roadmap to the database
        roadmap_document = {
            "userId": user_id,
            "skill": skill_name,
            "skill_slug": skill_name.lower().replace(" ", "-").replace("/", "-").replace(".", ""),
            "weeklyPlan": roadmap_data.get("weeklyPlan", []),
            "createdAt": datetime.utcnow()
        }
        roadmaps_collection.insert_one(roadmap_document)

        print(f"✅ Successfully generated and saved roadmap for user {user_id} and skill {skill_name}")
        return {"status": "success", "message": "Roadmap generated and saved."}

    except json.JSONDecodeError as e:
        print(f"!!! WORKER ERROR: Failed to decode JSON from Gemini API. Response was: {response.text}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="Failed to parse AI response.")
    except Exception as e:
        print(f"!!! WORKER ERROR: An unexpected error occurred: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"An internal worker error occurred: {e}")