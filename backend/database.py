# backend/database.py

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from the .env file for local development
load_dotenv()

# Get the MongoDB connection string from environment variables
MONGO_URI = os.getenv("MONGODB_URI")

# This is a best practice: create a single client instance and reuse it
try:
    client = MongoClient(MONGO_URI)
    # The 'db' object will be the interface to our database.
    # We can name our database anything we want, e.g., "learn_n_teach_db"
    db = client.learn_n_teach_db
    # The 'users_collection' will store all our user documents.
    users_collection = db.users
    print("✅ MongoDB connection successful.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    client = None
    users_collection = None