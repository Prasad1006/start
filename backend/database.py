import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

client = None
db = None
users_collection = None
roadmaps_collection = None
roadmap_requests_collection = None # For the dramatiq architecture

MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    print("!!! FATAL: MONGODB_URI not set.", file=sys.stderr)
else:
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ismaster')
        db = client.learn_n_teach_db
        users_collection = db.users
        roadmaps_collection = db.roadmaps
        roadmap_requests_collection = db.roadmap_requests
        print("✅ DB connection successful and collections assigned.", file=sys.stderr)
    except Exception as e:
        print(f"!!! FATAL DB ERROR: {e}", file=sys.stderr)