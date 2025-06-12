# backend/src/core/security.py

import os
from fastapi import Depends, HTTPException, status, Request
from jose import jwt, JWTError
import requests
from dotenv import load_dotenv

# Load environment variables for local development, specifically the Clerk issuer URL.
load_dotenv()

# Get the Clerk Issuer URL from the environment. This is a critical piece of the security puzzle.
# It tells our backend who the trusted authority is for issuing tokens.
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")


# This is a reusable dependency that can be used by any API endpoint
# to require a valid, logged-in user.
async def get_current_user(request: Request) -> dict:
    """
    Validates the JWT token from the Authorization header and returns the user payload.
    This acts as a "gatekeeper" for protected API routes.

    It performs the following checks:
    1. Ensures a "Bearer" token exists in the Authorization header.
    2. Fetches the public keys from Clerk's JWKS (JSON Web Key Set) endpoint.
    3. Finds the correct public key to match the incoming token.
    4. Decodes and verifies the token's signature, expiration date, and issuer claim.

    If any check fails, it raises an HTTPException, immediately stopping the request.
    If all checks pass, it returns the token's payload (a dictionary with user info).
    """
    if not CLERK_JWT_ISSUER:
        # This is a server configuration error, not a user error.
        # The application cannot function without this setting.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication provider not configured on the server."
        )
        
    # Get the token from the "Bearer <token>" header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing or malformed."
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Fetch the public keys from Clerk's JWKS endpoint
        jwks_url = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
        jwks = requests.get(jwks_url).json()
        
        # Get the header from the unverified token to find the correct key ('kid')
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = next((key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]), None)
        
        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key in JWKS to verify token."
            )
            
        # Decode and verify the token's signature, issuer, and claims
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            issuer=CLERK_JWT_ISSUER
        )
        # If successful, the payload (a dictionary with user info) is returned
        return payload

    except JWTError as e:
        # This catches errors like an expired token or invalid signature
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}"
        )
    except Exception as e:
        # Catch any other unexpected errors during validation
        # (e.g., Clerk's JWKS endpoint is down)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during token validation: {e}"
        )