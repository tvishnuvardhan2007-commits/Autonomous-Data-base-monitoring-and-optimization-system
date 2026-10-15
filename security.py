"""Simple bearer-token dependency for FastAPI; use an identity provider for production."""
from __future__ import annotations
import hmac, os
from fastapi import Header, HTTPException, status

def require_api_token(authorization: str | None = Header(default=None)) -> str:
    expected_token = os.getenv("API_TOKEN", "")
    if not expected_token:
        # Fail closed in production mode; never silently treat an unset token as auth.
        if os.getenv("APP_MODE", "demo").lower() in {"prod", "production"}:
            raise HTTPException(status_code=503, detail="Authentication is not configured.")
        return "demo-operator"
    supplied = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
    if not supplied or not hmac.compare_digest(supplied, expected_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing bearer token.")
    return "token-operator"
