from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Custom Exceptions ---

class TokenError(Exception):
    """Base token error."""
    pass


class TokenExpiredError(TokenError):
    """Token has expired."""
    pass


class InvalidTokenError(TokenError):
    """Token is invalid or malformed."""
    pass


class WrongTokenTypeError(TokenError):
    """Token type does not match expected type."""
    def __init__(self, expected: str, got: str | None):
        self.expected = expected
        self.got = got
        super().__init__(f"Expected token type '{expected}', got '{got}'")


# --- Token Creation ---

def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# --- Token Verification ---

def verify_token(token: str, expected_type: str | None = None) -> dict:
    """Verify and decode a JWT token.
    
    Args:
        token: The JWT token string.
        expected_type: If set, validates the 'type' claim matches.
    
    Returns:
        The decoded payload dict.
    
    Raises:
        TokenExpiredError: Token has expired.
        InvalidTokenError: Token is invalid/malformed.
        WrongTokenTypeError: Token type doesn't match expected_type.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except JWTError:
        raise InvalidTokenError("Invalid token")

    if expected_type is not None:
        token_type = payload.get("type")
        if token_type != expected_type:
            raise WrongTokenTypeError(expected=expected_type, got=token_type)

    return payload


def get_token_ttl_seconds(token: str) -> int:
    """Get remaining TTL in seconds for a token (for blacklist expiry)."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
        exp = payload.get("exp", 0)
        remaining = int(exp - datetime.now(timezone.utc).timestamp())
        return max(remaining, 0)
    except JWTError:
        return 0


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)
