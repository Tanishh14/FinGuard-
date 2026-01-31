"""
Pydantic schemas for authentication
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """Schema for JWT token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in_minutes: int = Field(..., description="Token expiry in minutes")
