from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from . import schemas, auth
from . import models as db_models
from .database import get_db
from .config import get_settings

settings = get_settings()
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, username, and password",
)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user

    - **email**: Valid email address (must be unique)
    - **username**: Username (3-50 characters, must be unique)
    - **password**: Strong password (minimum 8 characters)

    Returns the created user information
    """
    # Check if user with email or username already exists
    existing_user = (
        db.query(db_models.User)
        .filter(
            (db_models.User.email == user.email)
            | (db_models.User.username == user.username)
        )
        .first()
    )

    if existing_user:
        if existing_user.email == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )

    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    new_user = db_models.User(
        email=user.email, username=user.username, hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@auth_router.post(
    "/login",
    response_model=schemas.TokenResponse,
    summary="Login user (OAuth2 compatible)",
    description="Authenticate user with OAuth2 password flow (for Swagger UI authorization)",
)
def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    OAuth2 compatible login endpoint (used by Swagger UI "Authorize" button)

    - **username**: Username or email address
    - **password**: User password

    Returns access token (no refresh token support in this endpoint)
    """
    # Authenticate user
    user = auth.authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support.",
        )

    # Create access token
    access_token = auth.create_access_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # ✅ Added this field
    }


@auth_router.post(
    "/login/json",
    response_model=schemas.TokenResponse,
    summary="Login user (JSON)",
    description="Authenticate user and return access token (and refresh token if remember_me is True)",
)
def login_json(
    login_data: schemas.LoginRequest, request: Request, db: Session = Depends(get_db)
):
    """
    JSON-based login with refresh token support

    - **username**: Username or email address
    - **password**: User password
    - **remember_me**: If True, returns a long-lived refresh token (30 days)

    Returns access token and optionally refresh token
    """
    # Authenticate user
    user = auth.authenticate_user(login_data.username, login_data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support.",
        )

    # Create access token
    access_token = auth.create_access_token(data={"sub": user.username})

    # Create refresh token if remember_me is True
    refresh_token = None
    if login_data.remember_me:
        user_agent = request.headers.get("user-agent")
        # Get client IP (consider proxy headers in production)
        client_ip = request.client.host if request.client else None
        refresh_token = auth.create_refresh_token(
            user.id, db, user_agent=user_agent, ip_address=client_ip
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@auth_router.post(
    "/refresh",
    response_model=schemas.TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token",
)
def refresh_access_token(
    refresh_data: schemas.RefreshTokenRequest, db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token

    - **refresh_token**: Valid refresh token obtained from login

    Returns a new access token
    """
    user_id = auth.verify_refresh_token(refresh_data.refresh_token, db)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.query(db_models.User).filter(db_models.User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
        )

    # Create new access token
    access_token = auth.create_access_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@auth_router.post(
    "/logout",
    response_model=schemas.MessageResponse,
    summary="Logout user",
    description="Revoke the refresh token to logout user",
)
def logout(refresh_data: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Logout by revoking the refresh token

    - **refresh_token**: Refresh token to revoke

    Note: Access tokens will remain valid until expiration.
    For immediate token invalidation, implement token blacklisting.
    """
    revoked = auth.revoke_refresh_token(refresh_data.refresh_token, db)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Refresh token not found"
        )

    return {"message": "Successfully logged out"}


@auth_router.post(
    "/logout-all",
    response_model=schemas.MessageResponse,
    summary="Logout from all devices",
    description="Revoke all refresh tokens for the current user",
)
async def logout_all(
    current_user: db_models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Logout from all devices by revoking all refresh tokens

    Requires authentication with access token.
    """
    count = auth.revoke_all_user_tokens(current_user.id, db)

    return {"message": f"Successfully logged out from {count} device(s)"}


@auth_router.get(
    "/me",
    response_model=schemas.UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's information",
)
async def get_current_user_info(
    current_user: db_models.User = Depends(auth.get_current_active_user),
):
    """
    Get current authenticated user's information

    Requires a valid access token in the Authorization header.
    """
    return current_user


@auth_router.put(
    "/change-password",
    response_model=schemas.MessageResponse,
    summary="Change password",
    description="Change the password for the current user",
)
async def change_password(
    password_data: schemas.PasswordChangeRequest,
    current_user: db_models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Change user password

    - **current_password**: Current password for verification
    - **new_password**: New password (minimum 8 characters)

    Requires authentication. All refresh tokens will be revoked after password change.
    """
    # Verify current password
    if not auth.verify_password(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    current_user.hashed_password = auth.get_password_hash(password_data.new_password)
    db.commit()

    # Revoke all refresh tokens for security
    auth.revoke_all_user_tokens(current_user.id, db)

    return {"message": "Password changed successfully. Please login again."}


@auth_router.delete(
    "/delete-account",
    response_model=schemas.MessageResponse,
    summary="Delete user account",
    description="Permanently delete the current user's account",
)
async def delete_account(
    current_user: db_models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete user account permanently

    This action cannot be undone. All user data will be deleted.
    """
    # Revoke all tokens
    auth.revoke_all_user_tokens(current_user.id, db)

    # Delete user
    db.delete(current_user)
    db.commit()

    return {"message": "Account deleted successfully"}
