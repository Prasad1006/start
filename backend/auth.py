# backend/auth.py (FINAL BULLETPROOF VERSION)
import os
import sys
import requests
from fastapi import Request, HTTPException, status
from jose import jwt, jwk, JWTError
from jose.exceptions import JWKError
from dotenv import load_dotenv

load_dotenv()

CLERK_ISSUER_ID = os.getenv("CLERK_JWT_ISSUER")
JWKS_URL = f"{CLERK_ISSUER_ID}/.well-known/jwks.json"

async def get_current_user(request: Request) -> dict:
    """
    Validates a Clerk-issued JWT from the Authorization header and returns the claims.
    This version is designed to be highly robust for Vercel's serverless environment.
    """
    if not CLERK_ISSUER_ID:
        print("!!! AUTH-FATAL: Clerk JWT Issuer not configured.", file=sys.stderr)
        raise HTTPException(status_code=500, detail="Authentication service is not configured.")

    try:
        # 1. Get the token from the header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization scheme.")
        token = auth_header.split(' ')[-1]

        # 2. Fetch the public keys from Clerk (JWKS)
        response = requests.get(JWKS_URL)
        response.raise_for_status() # Raise exception for 4xx/5xx responses
        jwks = response.json()

        # 3. Get the 'kid' (Key ID) from the unverified token header
        unverified_header = jwt.get_unverified_header(token)
        if 'kid' not in unverified_header:
            raise HTTPException(status_code=401, detail="Malformed token: 'kid' not found in header.")
        
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                # Construct the key in the format python-jose expects
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Token's signing key not found in JWKS.")
            
        # 4. Decode and validate the token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            issuer=CLERK_ISSUER_ID
        )
        return payload

    except HTTPException as e:
        print(f"!!! AUTH-HTTP-FAIL: {e.status_code} - {e.detail}", file=sys.stderr)
        raise e
    except (JWTError, JWKError) as e:
        print(f"!!! AUTH-JWT-FAIL: {e}", file=sys.stderr)
        raise HTTPException(status_code=401, detail=f"Invalid Token: {e}")
    except requests.exceptions.RequestException as e:
        print(f"!!! AUTH-NETWORK-FAIL: Could not fetch public keys: {e}", file=sys.stderr)
        raise HTTPException(status_code=503, detail="Auth service unavailable.")
    except Exception as e:
        print(f"!!! AUTH-UNEXPECTED-FAIL: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during authentication.")