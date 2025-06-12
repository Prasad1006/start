# backend/database.py (fully updated version)
import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
from dotenv import load_dotenv

load_dotenv()

# --- Initialize variables to None for safety ---
client = None
db = None
users_collection = None
roadmaps_collection = None # <<< ADDED
sessions_collection = None

# --- Get the connection string from environment variables ---
MONGO_URI = os.getenv("MONGODB_URI")

# --- Attempt to connect with clear startup logging ---
if not MONGO_URI:
    print("!!! FATAL STARTUP ERROR: MONGODB_URI environment variable is NOT SET.", file=sys.stderr)
else:
    try:
        print("Attempting to connect to MongoDB...", file=sys.stderr)
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Force a connection test
        client.admin.command('ismaster')
        print("✅ MongoDB connection successful.", file=sys.stderr)
        
        db = client.learn_n_teach_db
        users_collection = db.users
        roadmaps_collection = db.roadmaps # <<< ADDED
        sessions_collection = db.sessions
        print("✅ Database collections initialized.", file=sys.stderr)

    except (ConnectionFailure, ConfigurationError) as e:
        print(f"!!! FATAL DB CONNECTION ERROR: Could not connect to MongoDB. CHECK YOUR CONNECTION STRING AND IP WHITELIST.", file=sys.stderr)
    except Exception as e:
        print(f"!!! FATAL UNEXPECTED DB ERROR during startup: {e}", file=sys.stderr)