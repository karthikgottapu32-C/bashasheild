import hashlib
import hmac
import secrets
import base64
import json
import time
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from fastapi import Header, HTTPException, Depends
from app.config import settings
from app.database import is_token_revoked, revoke_token

# OWASP Recommended Work Factors
PBKDF2_ITERATIONS = 600_000
LEGACY_PBKDF2_ITERATIONS = 100_000
SALT_SIZE_BYTES = 16

JWT_ISSUER = "bhashashield-api"
JWT_AUDIENCE = "bhashashield-client"


def validate_password_complexity(password: str) -> Tuple[bool, str]:
    """
    Enforces minimum security requirements on user passwords:
    - Minimum length: 8 characters
    - Maximum length: 128 characters
    - Requires at least one letter (a-z, A-Z)
    - Requires at least one digit (0-9) or symbol
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password must not exceed 128 characters."
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"[\d\W_]", password):
        return False, "Password must contain at least one digit or special character."
    return True, "Valid"


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with 600,000 iterations (OWASP modern standard)
    and a 16-byte cryptographically secure random salt.
    Format: pbkdf2-sha256$600000$salt_hex$key_hex
    """
    salt = secrets.token_bytes(SALT_SIZE_BYTES)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2-sha256${PBKDF2_ITERATIONS}${salt.hex()}${key.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """
    Verifies password against stored hash in constant time.
    Supports both:
    1. Upgraded 4-part format: pbkdf2-sha256$iterations$salt$hash
    2. Legacy 2-part format: salt$hash (100,000 iterations)
    """
    try:
        if hashed.startswith("pbkdf2-sha256$"):
            _, iter_str, salt_hex, key_hex = hashed.split("$", 3)
            iterations = int(iter_str)
            salt = bytes.fromhex(salt_hex)
            expected_key = bytes.fromhex(key_hex)
            key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(key, expected_key)
        else:
            # Legacy 2-part format from earlier release
            salt_hex, key_hex = hashed.split("$", 1)
            salt = bytes.fromhex(salt_hex)
            expected_key = bytes.fromhex(key_hex)
            key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, LEGACY_PBKDF2_ITERATIONS)
            return hmac.compare_digest(key, expected_key)
    except Exception:
        return False


def password_needs_rehash(hashed: str) -> bool:
    """
    Detects whether an authenticated password hash needs to be transparently upgraded
    to the current OWASP 600,000-iteration standard.
    """
    if not hashed.startswith("pbkdf2-sha256$"):
        return True
    try:
        _, iter_str, _, _ = hashed.split("$", 3)
        return int(iter_str) < PBKDF2_ITERATIONS
    except Exception:
        return True


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding and padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(
    user_id: str,
    username: str,
    role: str = "user",
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generates a cryptographically signed, compliant session JWT containing standard claims:
    - iss (issuer): bhashashield-api
    - aud (audience): bhashashield-client
    - sub (subject): user_id
    - username: sanitized username
    - role: user role
    - jti: unique token UUID (for server-side revocation)
    - iat, nbf, exp: timestamps
    Zero sensitive data (passwords, salts, secrets) is included.
    """
    now = int(time.time())
    if expires_delta:
        exp = int(now + expires_delta.total_seconds())
    else:
        exp = int(now + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60))
    
    jti = f"jwt_{uuid.uuid4().hex}"
    
    payload = {
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "sub": user_id,
        "username": username,
        "role": role,
        "jti": jti,
        "iat": now,
        "nbf": now,
        "exp": exp
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
    """
    Decodes and validates token:
    1. Signature verification in constant time
    2. Expiration and Not-Before checks
    3. Issuer and Audience validation
    4. Server-side revocation verification
    """
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
        now = time.time()
        
        # Expiration check
        if payload.get("exp", 0) < now:
            return None
        
        # Not-before check
        if payload.get("nbf", 0) > now + 5:  # 5s clock skew tolerance
            return None
        
        # Issuer check (if present)
        if payload.get("iss") and payload.get("iss") != JWT_ISSUER:
            return None
            
        # Audience check (if present)
        if payload.get("aud") and payload.get("aud") != JWT_AUDIENCE:
            return None
        
        # Server-side revocation check
        jti = payload.get("jti")
        if jti and is_token_revoked(jti):
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
    """FastAPI dependency requiring a valid, non-revoked Bearer token."""
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
