import os
import dramatiq
import json
import google.generativeai as genai
from dramatiq.brokers.redis import RedisBroker
from pymongo import MongoClient
from datetime import datetime
from urllib.parse import quote

UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
if not UPSTASH_REDIS_URL: raise RuntimeError("UPSTASH_REDIS_URL is not set.")

redis_broker = RedisBroker(url=UPSTASH_REDIS_URL)
dramatiq.set_broker(redis_broker)

@dramatiq.actor(max_retries=1)
def generate_roadmap_task(user_id: str, skill_name: str):
    MONGO_URI = os.getenv("MONGODB_URI")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not MONGO_URI or not GEMINI_API_KEY:
        print("!!! TASK ERROR: Missing DB or Gemini environment variables.")
        return

    mongo_client = None
    try:
        mongo_client = MongoClient(MONGO_URI)
        roadmaps_collection = mongo_client.learn_n_teach_db.roadmaps
        genai.configure(api_key=GEMINI_API_KEY)
        
        prompt = f"""Act as an expert curriculum designer. Create a detailed, 8-week learning roadmap for the skill: "{skill_name}". The output must be a valid JSON object with a single "weeklyPlan" key containing an array of objects. Each weekly object needs keys: "week" (number), "topic" (string), "description" (string), and "status" (string, initially "PENDING")."""

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        roadmap_data = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        
        safe_skill_slug = quote(skill_name.lower().replace(" ", "-").replace("/", "-"), safe='')
        doc = { "userId": user_id, "skill": skill_name, "skill_slug": safe_skill_slug, "weeklyPlan": roadmap_data.get("weeklyPlan", []), "createdAt": datetime.utcnow() }
        
        roadmaps_collection.insert_one(doc)
        print(f"✅ Successfully generated roadmap for user {user_id}")
    except Exception as e:
        print(f"!!! TASK FAILED for user {user_id}: {e}")
    finally:
        if mongo_client:
            mongo_client.close()