"""
Authentication and Password Security Utilities
Handles Bcrypt password hashing, verification, and JWT token issuance.
Works for all Actors: Farmers, Buyers, Drivers, Admins, Hub Staff.
"""

import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

# JWT Secret & Configuration
JWT_SECRET_KEY = "krishilink_super_secure_jwt_secret_key_2026_pilot"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
DEFAULT_DEMO_PASSWORD = "123456"

def hash_password(plain_password: str) -> str:
    """Hash a plain text password using bcrypt with salt."""
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(user_id: str, role: str, phone: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generate signed JWT access token for API authentication."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    payload = {
        "sub": user_id,
        "role": role,
        "phone": phone,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "krishilink-platform"
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return decoded
    except jwt.PyJWTError:
        return None
