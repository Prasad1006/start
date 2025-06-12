# backend/auth.py
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

try:
    jwks = requests.get(JWKS_URL).json()
except requests.exceptions.RequestException as e:
    raise RuntimeError(f"Could not fetch Clerk JWKS: {e}")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {"kty": key["kty"], "kid": key["kid"], "use": key["use"], "n": key["n"], "e": key["e"]}
                break
        
        if not rsa_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token's signing key not found.")

        payload = jwt.decode(token, rsa_key, algorithms=["RS256"], issuer=CLERK_ISSUER_URL)
        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )