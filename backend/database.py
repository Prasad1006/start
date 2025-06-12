# backend/database.py
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
sessions_collection = None

MONGO_URI = os.getenv("MONGODB_URI")

if not MONGO_URI:
    print("!!! FATAL: MONGODB_URI not set.", file=sys.stderr)
else:
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ismaster')
        print("✅ DB connection successful.", file=sys.stderr)
        
        db = client.learn_n_teach_db
        users_collection = db.users
        roadmaps_collection = db.roadmaps
        sessions_collection = db.sessions
        print("✅ DB collections initialized.", file=sys.stderr)

    except ConnectionFailure as e:
        print(f"!!! FATAL DB ERROR: Could not connect to MongoDB: {e}", file=sys.stderr)
    except Exception as e:
        print(f"!!! FATAL UNEXPECTED DB ERROR: {e}", file=sys.stderr)