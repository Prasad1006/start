# backend/src/core/security.py

import os
from fastapi import Depends, HTTPException, status, Request
from jose import jwt, JWTError
import requests
from dotenv import load_dotenv

# Load environment variables for local development.
load_dotenv()

# Get the Clerk Issuer URL from the environment. This is critical for token validation.
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")

# This is a reusable dependency that acts as a "gatekeeper" for protected API routes.
async def get_current_user(request: Request) -> dict:
    """
    Validates the JWT token from the Authorization header and returns the user payload.
    If the token is invalid or missing, it raises an HTTPException.
    """
    if not CLERK_JWT_ISSUER:
        raise HTTPException(status_code=500, detail="Authentication provider not configured on the server.")
        
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header is missing or malformed.")
    
    token = auth_header.split(" ")[1]
    
    try:
        jwks_url = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
        jwks = requests.get(jwks_url).json()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = next((key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]), None)
        
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Unable to find appropriate key in JWKS to verify token.")
            
        payload = jwt.decode(
            token, rsa_key, algorithms=["RS256"], issuer=CLERK_JWT_ISSUER
        )
        return payload

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during token validation: {e}")