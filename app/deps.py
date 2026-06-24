# app/deps.py
#
# Shared FastAPI dependencies.
#
# Auth pattern for new routers:
#   from app.deps import get_current_user
#   def endpoint(current_user = Depends(get_current_user)):
#       user_id = current_user["user_id"]

from __future__ import annotations

from typing import Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from jose import ExpiredSignatureError, JWTError

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.auth_manager import auth_manager

# Auto-extract Bearer token from Authorization header
# auto_error=True → FastAPI returns 401 automatically if header is missing
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=True)


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Validate JWT token and return current user payload.

    Returns:
        dict with 'user_id' (from 'sub') and 'email'

    Raises:
        401 Not authenticated — missing header (auto_error)
        401 Token expired — JWT signature valid but expired
        401 Invalid credentials — malformed or wrong signature
    """
    try:
        payload = auth_manager.decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Normalize payload to include 'user_id' key (from 'sub')
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
    }
