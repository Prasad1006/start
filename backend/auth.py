# backend/auth.py (FINAL, SIMPLIFIED AND CORRECTED VERSION)
import os
import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

CLERK_ISSUER_URL = os.getenv("CLERK_JWT_ISSUER")
if not CLERK_ISSUER_URL:
    raise RuntimeError("CLERK_JWT_ISSUER environment variable not set.")

JWKS_URL = f"{CLERK_ISSUER_URL}/.well-known/jwks.json"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Fetch the JWKS from Clerk once when the application starts.
# This avoids making an HTTP request on every single API call, which is much more performant.
try:
    jwks = requests.get(JWKS_URL).json()
except requests.exceptions.RequestException as e:
    # If we can't get the keys on startup, the app can't function.
    raise RuntimeError(f"Could not fetch Clerk JWKS: {e}")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    A dependency that validates a Clerk JWT and returns its claims (payload).
    It uses the pre-fetched JWKS for verification.
    """
    try:
        # Get the 'kid' (Key ID) from the unverified token header.
        unverified_header = jwt.get_unverified_header(token)
        
        # Find the public key in the JWKS that matches the token's 'kid'.
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
                break
        
        if not rsa_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token's signing key not found.")

        # Decode and validate the token.
        # jwt.decode will automatically verify:
        # - The token's signature using the rsa_key.
        # - The token's expiration time ('exp' claim).
        # - The token's issuer ('iss' claim).
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            issuer=CLERK_ISSUER_URL
        )
        return payload

    except JWTError as e:
        # This will be raised if the token is expired, has an invalid signature, etc.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )