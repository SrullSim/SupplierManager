from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.security import JWTError, decode_token

bearer = HTTPBearer()


def _get_payload(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expected access token")
    return payload


def get_current_user(payload: dict = Depends(_get_payload)) -> dict:
    return payload


def require_factory_admin(payload: dict = Depends(get_current_user)) -> dict:
    if payload.get("role") != "factory_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Factory admin required")
    return payload


def require_branch_user(payload: dict = Depends(get_current_user)) -> dict:
    if payload.get("role") != "branch_user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Branch user required")
    return payload
