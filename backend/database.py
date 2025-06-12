# backend/database.py (FINAL STABLE VERSION)
import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

# --- Initialize variables to None for safety ---
client = None
db = None
users_collection = None
roadmaps_collection = None
sessions_collection = None
roadmap_requests_collection = None

# --- Get the connection string from environment variables ---
MONGO_URI = os.getenv("MONGODB_URI")

# --- Attempt to connect with clear startup logging ---
if not MONGO_URI:
    print("!!! FATAL STARTUP ERROR: MONGODB_URI environment variable is NOT SET.", file=sys.stderr)
else:
    try:
        print("--- [DB] Attempting to connect to MongoDB... ---", file=sys.stderr)
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Force a connection test
        client.admin.command('ismaster')
        print("✅ [DB] MongoDB connection successful.", file=sys.stderr)
        
        db = client.learn_n_teach_db
        users_collection = db.users
        roadmaps_collection = db.roadmaps
        sessions_collection = db.sessions
        roadmap_requests_collection = db.roadmap_requests
        print("✅ [DB] Database collections initialized.", file=sys.stderr)

    except ConnectionFailure as e:
        print(f"!!! FATAL DB CONNECTION ERROR: Could not connect to MongoDB: {e}", file=sys.stderr)
    except Exception as e:
        print(f"!!! FATAL UNEXPECTED DB ERROR during startup: {e}", file=sys.stderr)