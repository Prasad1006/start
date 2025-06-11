import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from dotenv import load_dotenv

# Load environment variables for local development
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
client = None
db = None
users_collection = None
roadmaps_collection = None
sessions_collection = None
quizzes_collection = None
feedback_collection = None

# This check runs ONCE when the serverless function starts (cold start)
if not MONGO_URI:
    # This will show up clearly in Vercel logs if the variable is missing
    print("!!! FATAL STARTUP ERROR: MONGODB_URI environment variable is NOT SET.", file=sys.stderr)
else:
    try:
        # Set a timeout to fail faster if the network connection is bad
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # The ismaster command is a lightweight way to test the connection
        client.admin.command('ismaster')
        print("✅ MongoDB connection successful during startup.", file=sys.stderr)
        
        # Define all our collections in one place
        db = client.learn_n_teach_db
        users_collection = db.users
        roadmaps_collection = db.roadmaps
        sessions_collection = db.sessions
        quizzes_collection = db.quizzes
        feedback_collection = db.feedback

    except ConfigurationError as e:
        print(f"!!! FATAL DB CONFIGURATION ERROR: Could not connect to MongoDB. Check your connection string and IP whitelist.", file=sys.stderr)
        print(f"DETAILS: {e}", file=sys.stderr)
    except Exception as e:
        print(f"!!! FATAL UNEXPECTED DB ERROR during startup: {e}", file=sys.stderr)