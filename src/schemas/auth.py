from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    fullname: str = Field(..., min_length=1, max_length=100, description="Full name of the user")
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Valid email address")
    password: str = Field(..., min_length=6, description="Password of at least 6 characters")
    mobile_number: Optional[str] = Field(None, max_length=20)
    role: Optional[str] = Field("Customer", description="User role (Customer, Support Specialist, Tier 2 Support, Lead Support Agent)")
    tenant_id: Optional[str] = Field("default", description="Tenant or organization identifier")

class UserLoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class GuestLoginRequest(BaseModel):
    fullname: Optional[str] = Field("Guest User", description="Display name for guest session")
    tenant_id: Optional[str] = Field("default", description="Tenant identifier for isolation")

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: str
    username: str
    fullname: str
    role: str
    tenant_id: str
    is_guest: bool = False
    expires_in: int = Field(default=7200, description="Access token expiration in seconds")

class UserResponse(BaseModel):
    user_id: str
    username: str
    fullname: str
    email: Optional[str] = None
    mobile_number: Optional[str] = None
    role: str
    tenant_id: str
    is_guest: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
