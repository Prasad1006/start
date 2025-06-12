# backend/tasks.py (NEW FILE FOR BACKGROUND JOBS)
import os
import dramatiq
import json
import google.generativeai as genai
from dramatiq.brokers.redis import RedisBroker
from pymongo import MongoClient
from datetime import datetime
from urllib.parse import quote

# 1. Set up the connection to Redis (our message broker)
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
redis_broker = RedisBroker(url=UPSTASH_REDIS_URL)
dramatiq.set_broker(redis_broker)

# 2. Set up the DB connection *within* the worker
MONGO_URI = os.getenv("MONGODB_URI")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client.learn_n_teach_db
roadmaps_collection = db.roadmaps

@dramatiq.actor
def generate_roadmap_task(user_id: str, skill_name: str):
    """
    This is the dramatiq actor that runs as a background task.
    """
    print(f"--- Starting roadmap generation task for user {user_id}, skill: {skill_name} ---")
    
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("!!! TASK-ERROR: GEMINI_API_KEY env var not set.")
        return # Exit gracefully

    try:
        genai.configure(api_key=gemini_api_key)
        
        prompt = f"""Act as an expert curriculum designer... for "{skill_name}"...""" # Use your full prompt

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt) # Use the synchronous method here
        roadmap_data = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        
        safe_skill_slug = quote(skill_name.lower().replace(" ", "-"), safe='')
        doc = {
            "userId": user_id, "skill": skill_name, "skill_slug": safe_skill_slug,
            "weeklyPlan": roadmap_data.get("weeklyPlan", []), "createdAt": datetime.utcnow()
        }
        
        roadmaps_collection.insert_one(doc)
        print(f"✅ Successfully generated roadmap for user {user_id}, skill: {skill_name}")
    
    except Exception as e:
        # Log the error. In a real app, you'd add this to a "failed_jobs" collection.
        print(f"!!! TASK-ERROR: Failed to generate roadmap for {user_id}. Reason: {e}")