import os
import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

CLERK_ISSUER_URL = os.getenv("CLERK_JWT_ISSUER")
if not CLERK_ISSUER_URL: raise RuntimeError("CLERK_JWT_ISSUER env var not set.")

JWKS_URL = f"{CLERK_ISSUER_URL}/.well-known/jwks.json"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

try:
    jwks = requests.get(JWKS_URL).json()
except Exception as e:
    raise RuntimeError(f"Could not fetch Clerk JWKS on startup: {e}")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = next((key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]), None)
        if not rsa_key: raise HTTPException(status_code=401, detail="Token's signing key not found.")
        
        payload = jwt.decode(token, rsa_key, algorithms=["RS256"], issuer=CLERK_ISSUER_URL)
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=str(e), headers={"WWW-Authenticate": "Bearer"})