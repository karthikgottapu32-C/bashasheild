import hashlib
import hmac
import secrets
import base64
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, Depends
from app.config import settings

def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with 100,000 rounds and a 16-byte random salt."""
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${key.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against stored salt$hash in constant time."""
    try:
        salt_hex, key_hex = hashed.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(key, expected_key)
    except Exception:
        return False

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def _b64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding and padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))

def create_access_token(user_id: str, username: str, role: str = "user", expires_delta: Optional[timedelta] = None) -> str:
    """Generates a cryptographically signed, compact session token."""
    now = time.time()
    if expires_delta:
        exp = now + expires_delta.total_seconds()
    else:
        exp = now + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "iat": int(now),
        "exp": int(exp)
    }
    payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = _b64url_encode(payload_json)
    
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256
    ).digest()
    sig_b64 = _b64url_encode(signature)
    
    return f"{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates token signature and expiration in constant time."""
    try:
        parts = token.split(".", 1)
        if len(parts) != 2:
            return None
        payload_b64, sig_b64 = parts
        
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256
        ).digest()
        
        actual_sig = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        
        payload_json = _b64url_decode(payload_b64)
        payload = json.loads(payload_json.decode("utf-8"))
        
        # Check expiration
        if payload.get("exp", 0) < time.time():
            return None
        
        return payload
    except Exception:
        return None

def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """FastAPI dependency to optionally authenticate user via Bearer token."""
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return decode_access_token(token.strip())

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """FastAPI dependency requiring valid Bearer token."""
    user = get_optional_user(authorization)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide a valid Bearer token in the Authorization header.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

def require_admin(
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")
) -> bool:
    """
    Validates administrative authorization via either:
    1. X-Admin-Key header matching ADMIN_API_KEY
    2. Valid Bearer token with role == 'admin'
    """
    if settings.ADMIN_API_KEY and x_admin_key == settings.ADMIN_API_KEY:
        return True
    
    user = get_optional_user(authorization)
    if user and user.get("role") == "admin":
        return True
    
    raise HTTPException(
        status_code=401,
        detail="Administrative authorization required. Provide a valid X-Admin-Key or admin token."
    )
