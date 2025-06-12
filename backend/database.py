# backend/database.py (FINAL ARCHITECTURE)
import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

class DB:
    client: MongoClient = None

db_instance = DB()

async def connect_to_mongo():
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        print("!!! FATAL: MONGODB_URI env var is not set.", file=sys.stderr)
        return

    print("--- Connecting to MongoDB... ---", file=sys.stderr)
    try:
        db_instance.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db_instance.client.admin.command('ismaster')
        print("✅ MongoDB connection successful.", file=sys.stderr)
    except ConnectionFailure as e:
        print(f"!!! FATAL: Could not connect to MongoDB: {e}", file=sys.stderr)
        db_instance.client = None

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        print("--- MongoDB connection closed. ---", file=sys.stderr)

def get_db_dependency():
    if db_instance.client is None:
        raise ConnectionFailure("Database connection not established.")
    return db_instance.client.learn_n_teach_db