# backend/auth.py (new file)
import os
import requests
from fastapi import Request, HTTPException
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")

async def get_current_user(request: Request) -> dict:
    """
    Dependency to get the current user from a Clerk-issued JWT.
    Verifies the token and returns the decoded claims.
    """
    if not CLERK_JWT_ISSUER:
        raise HTTPException(
            status_code=500,
            detail="Authentication issuer not configured on the server."
        )

    # The token is expected in the "Authorization" header as "Bearer <token>"
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization scheme.")
    
    token = auth_header.split(' ')[-1]

    try:
        # Fetch the JWKS (JSON Web Key Set) from Clerk
        jwks_url = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
        jwks = requests.get(jwks_url).json()

        # Get the header from the token without verification to find the matching key
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Unable to find corresponding public key.")

        # Decode the token, which also verifies the signature, expiration, and issuer
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            issuer=CLERK_JWT_ISSUER
        )
        return payload

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except (IndexError, requests.RequestException) as e:
         raise HTTPException(status_code=500, detail=f"Error fetching authentication keys: {e}")