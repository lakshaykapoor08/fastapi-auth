from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(..., description="The user's email address")
    username: str = Field(
        ..., min_length=3, max_length=50, description="The user's username"
    )
    password: str = Field(
        ..., min_length=8, description="The user's password(min 8 characters)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "SecurePassword123!",
            }
        }
    )


class UserResponse(BaseModel):
    """Schema for user response"""

    id: int
    email: str
    username: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """Schema for login request"""

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(
        default=False, description="Enable long-lived refresh token"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "password": "SecurePassword123!",
                "remember_me": True,
            }
        }
    )


class TokenResponse(BaseModel):
    """Schema for token response"""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(
        None, description="Refresh token (only if remember_me=True)"
    )
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "abc123def456ghi789...",
                "token_type": "bearer",
                "expires_in": 1800,
            }
        }
    )


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""

    refresh_token: str = Field(..., description="Valid refresh token")

    model_config = ConfigDict(
        json_schema_extra={"example": {"refresh_token": "abc123def456ghi789..."}}
    )


class MessageResponse(BaseModel):
    """Generic message response"""

    message: str = Field(..., description="Response message")

    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Operation completed successfully"}}
    )


class PasswordChangeRequest(BaseModel):
    """Schema for password change"""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., min_length=8, max_length=100, description="New password"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePassword456!",
            }
        }
    )
