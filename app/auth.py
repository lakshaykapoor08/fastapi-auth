from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import get_settings
from .database import get_db
from .models import User, RefreshToken
import secrets

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain password

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[int] = None
) -> str:
    """
    Create a JWT access token

    Args:
        data: Data to encode in the token
        expires_delta: Expiration time in minutes

    Returns:
        Encoded JWT token as a string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update(
        {"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"}
    )

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(
    user_id: int,
    db: Session,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> str:
    """
    Create a refresh token and store it in the database

    Args:
        user_id: User ID
        db: Database session
        user_agent: User agent string
        ip_address: Client IP address

    Returns:
        Refresh token string
    """
    # Generate secure random token
    token = secrets.token_urlsafe(32)

    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    # Store in database
    db_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    db.add(db_token)
    db.commit()
    db.refresh(db_token)

    return token


def verify_refresh_token(token: str, db: Session) -> Optional[int]:
    """
    Verify a refresh token and return the user ID if valid

    Args:
        token: Refresh token to verify
        db: Database session

    Returns:
        User ID if token is valid, None otherwise
    """

    db_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token == token,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )

    if db_token:
        return db_token.user_id

    return None


def revoke_all_user_tokens(user_id: int, db: Session) -> int:
    """
    Revoke all refresh tokens for a user

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Number of tokens revoked
    """
    tokens = (
        db.query(RefreshToken)
        .filter(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
        .all()
    )

    count = 0
    for token in tokens:
        token.is_revoked = True
        token.revoked_at = datetime.now(timezone.utc)
        count += 1

    db.commit()
    return count


def revoke_refresh_token(token: str, db: Session) -> bool:
    """
    Revoke a refresh token

    Args:
        token: Refresh token to revoke
        db: Database session

    Returns:
        True if token was revoked, False if token not found
    """
    db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()

    if db_token:
        db_token.is_revoked = True
        db_token.revoked_at = datetime.now(timezone.utc)
        db.commit()
        return True
    return False


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT access token

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from the JWT token

    Args:
        token: JWT access token
        db: Database session

    Returns:
        Current user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user

    Args:
        current_user: Current authenticated user

    Returns:
        Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


def authenticate_user(username: str, password: str, db: Session) -> Optional[User]:
    """
    Authenticate a user by username/email and password

    Args:
        username: Username or email
        password: Plain text password
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    # Try to find user by username or email
    user = (
        db.query(User)
        .filter((User.username == username) | (User.email == username))
        .first()
    )

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
