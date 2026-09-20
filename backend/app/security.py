import datetime
from typing import Optional, Any, Union
from jose import jwt, JWTError

# Ensure passlib 1.7.4 compatibility with bcrypt 4.1+
import bcrypt
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type("About", (), {"__version__": getattr(bcrypt, "__version__", "4.0.0")})()

from passlib.context import CryptContext
from backend.app.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against the stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a secure bcrypt hash for a plain-text password."""
    return pwd_context.hash(password)


def create_access_token(subject: Union[str, Any], role: str, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """
    Generate a signed JWT token containing the user ID as 'sub' and role.
    Defaults to ACCESS_TOKEN_EXPIRE_HOURS from config.
    """
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            hours=settings.ACCESS_TOKEN_EXPIRE_HOURS
        )

    to_encode = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
