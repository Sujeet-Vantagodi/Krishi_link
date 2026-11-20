import uuid
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict, SecretStr, field_validator
from app.models.enums import UserRole


class OtpRequest(BaseModel):
    phone: str = Field(max_length=24, description="Phone number with country code, e.g. +919876543210")
    role: Optional[UserRole] = Field(default=UserRole.BUYER, description="Role if user is new")

    @field_validator("phone")
    @classmethod
    def canonical_phone(cls, value: str) -> str:
        return normalize_phone(value)


class OtpRequestResponse(BaseModel):
    request_id: str
    message: str
    mock_otp: Optional[str] = None  # Returned only in dev / test mode


class OtpVerify(BaseModel):
    request_id: str = Field(max_length=64)
    otp: str = Field(pattern=r"^[0-9]{6}$")


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    phone: str
    role: UserRole
    name: Optional[str] = None
    language: str = "kn"
    is_active: bool = True
    needs_onboarding: bool = False
    email: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdate(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None


class PasswordLogin(BaseModel):
    phone: str = Field(max_length=24)
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return normalize_phone(value)


def normalize_phone(value: str) -> str:
    import re

    value = value.strip()
    if re.fullmatch(r"[0-9]{10}", value):
        value = "+91" + value
    if not re.fullmatch(r"\+91[0-9]{10}", value):
        raise ValueError("Enter a valid Indian mobile number")
    return value


class PasswordRegistration(PasswordLogin):
    password: SecretStr = Field(min_length=8, max_length=128)
    role: UserRole
    name: str = Field(min_length=1, max_length=120, pattern=r"\S")
    email: str | None = Field(default=None, max_length=120, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    business_name: str | None = Field(default=None, max_length=160)
    business_type: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=500)
    village: str | None = Field(default=None, max_length=120)
    taluk: str | None = Field(default=None, max_length=120)
    land_acres: float | None = Field(default=None, ge=0, le=9999.99)
    min_threshold_kg: float | None = Field(default=None, gt=0, le=999999.99)
