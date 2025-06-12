# backend/main.py (FINAL DIAGNOSTIC VERSION - SINGLE FILE)
import os
import sys
from fastapi import FastAPI, Response, Request, HTTPException
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import requests
from jose import jwt, JWTError

# --- 1. Load Environment and Set up Logging ---
load_dotenv()
app = FastAPI()

print("--- [SERVER START] Application module is being loaded. ---", file=sys.stderr)

# --- 2. Centralized Database Connection Logic ---
MONGO_URI = os.getenv("MONGODB_URI")
users_collection = None

if not MONGO_URI:
    print("!!! FATAL STARTUP ERROR: MONGODB_URI environment variable is NOT SET.", file=sys.stderr)
else:
    try:
        print("--- [DB] Attempting to create MongoClient... ---", file=sys.stderr)
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ismaster')
        db = client.learn_n_teach_db
        users_collection = db.users
        print("✅ [DB] MongoClient created and users_collection is assigned.", file=sys.stderr)
    except ConnectionFailure as e:
        print(f"!!! FATAL DB CONNECTION ERROR: Could not connect to MongoDB: {e}", file=sys.stderr)
    except Exception as e:
        print(f"!!! FATAL UNEXPECTED DB ERROR during startup: {e}", file=sys.stderr)


# --- 3. Self-Contained Authentication Logic ---
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")

async def get_current_user(request: Request) -> dict:
    if not CLERK_JWT_ISSUER:
        raise HTTPException(status_code=500, detail="Auth issuer not configured.")
    
    token = request.headers.get('Authorization', '').split(' ')[-1]
    
    try:
        jwks_url = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
        jwks = requests.get(jwks_url).json()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = next((key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]), None)
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Key not found")
        
        return jwt.decode(token, rsa_key, algorithms=["RS256"], issuer=CLERK_JWT_ISSUER)
    except (JWTError, IndexError) as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


# --- 4. THE FAILING ENDPOINT with Exhaustive Logging ---
@app.get("/api/users/onboarding-status")
async def get_onboarding_status(request: Request):
    print("--- [HANDLER START] Entering /api/users/onboarding-status ---", file=sys.stderr)
    
    try:
        # Step A: Get the current user
        current_user = await get_current_user(request)
        user_id = current_user.get("sub")
        print(f"[HANDLER] Successfully decoded token for user_id: {user_id}", file=sys.stderr)

        if not user_id:
             print("!!! [HANDLER ERROR] 'sub' claim not found in token.", file=sys.stderr)
             raise HTTPException(status_code=400, detail="'sub' claim missing from token.")

        # Step B: Check the database collection object
        if users_collection is None:
            print("!!! [HANDLER ERROR] users_collection object is None. DB connection likely failed on startup.", file=sys.stderr)
            raise HTTPException(status_code=503, detail="Database service not available.")
        
        print("[HANDLER] users_collection object is valid. Proceeding to query.", file=sys.stderr)

        # Step C: Perform the database query
        profile_document = users_collection.find_one({"userId": user_id}, {"_id": 1})

        print(f"[HANDLER] Database find_one query completed. Result: {profile_document}", file=sys.stderr)

        if profile_document:
            print("--- [HANDLER END] Profile found. Returning 'completed'. ---", file=sys.stderr)
            return {"status": "completed"}
        else:
            print("--- [HANDLER END] No profile found. Returning 'pending'. ---", file=sys.stderr)
            return {"status": "pending"}

    except HTTPException as e:
        # If we raised an HTTPException ourselves, re-raise it
        print(f"!!! [HANDLER HTTP EXCEPTION] {e.detail}", file=sys.stderr)
        raise e
    except Exception as e:
        # For any other unexpected crash
        print(f"!!! [HANDLER CRITICAL UNEXPECTED ERROR]: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="A critical unexpected error occurred.")

# --- 5. A Simple Test Endpoint ---
# This endpoint ignores all other logic to see if the server itself can run.
@app.get("/api/health")
def health_check():
    return {"status": "ok"}