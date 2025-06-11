# backend/database.py

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from the .env file for local development
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")

if not MONGO_URI:
    raise Exception("FATAL ERROR: MONGODB_URI environment variable is not set.")

try:
    # This is a best practice: create a single client instance and reuse it
    client = MongoClient(MONGO_URI)
    
    # Ping the server to check the connection
    client.admin.command('ping')
    print("✅ MongoDB connection successful.")
    
    # The 'db' object will be the interface to our database.
    db = client.learn_n_teach_db
    
    # Define all collections we will use in one place
    users_collection = db.users
    sessions_collection = db.sessions
    quizzes_collection = db.quizzes
    # ... and so on

except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    # Set to None so the app will fail loudly if the DB is down
    client = None
    users_collection = None
    sessions_collection = None
    quizzes_collection = None