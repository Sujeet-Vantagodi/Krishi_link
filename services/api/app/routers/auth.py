from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.schemas.auth import (
    OtpRequest, OtpRequestResponse, OtpVerify,
    RefreshTokenRequest, TokenResponse, UserResponse, UserUpdate
)
from app.services.auth_service import request_otp, verify_otp, refresh_user_token
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import create_access_token, create_refresh_token
from pydantic import BaseModel
from pathlib import Path
from sqlalchemy.engine import make_url

router = APIRouter(prefix="", tags=["Auth"])
legacy_auth_router = APIRouter(tags=["Auth"])


@legacy_auth_router.post("/api/auth/login", include_in_schema=False)
@legacy_auth_router.post("/api/auth/register", include_in_schema=False)
@router.post("/auth/login", include_in_schema=False)
@router.post("/auth/register", include_in_schema=False)
def password_auth_unavailable():
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Password authentication is unavailable until the credential store is integrated.",
    )

DEMO_ACCOUNTS = {
    UserRole.FARMER: "+919999001001",
    UserRole.BUYER: "+919999002001",
    UserRole.DRIVER: "+919999003001",
    UserRole.HUB_STAFF: "+919999004001",
    UserRole.ADMIN: "+919999005001",
    UserRole.SUPER_ADMIN: "+919999006001",
}


class DemoLoginIn(BaseModel):
    role: UserRole


@router.post("/auth/demo-login")
def api_demo_login(data: DemoLoginIn, db: Session = Depends(get_db)):
    configured_url = make_url(settings.DATABASE_URL)
    demo_db = Path(__file__).resolve().parents[2] / "krishilink_demo.db"
    if (not settings.demo_login_allowed or configured_url.drivername != "sqlite+pysqlite"
            or Path(configured_url.database or "").resolve() != demo_db.resolve()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    phone = DEMO_ACCOUNTS[data.role]
    user = db.query(User).filter(User.phone == phone, User.role == data.role, User.is_active.is_(True)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Demo accounts are not seeded")
    return {
        "access_token": create_access_token(user_id=user.id, role=user.role),
        "refresh_token": create_refresh_token(user_id=user.id, role=user.role),
        "token_type": "bearer",
        "user": {"id": str(user.id), "phone": user.phone, "role": user.role.value, "name": user.name, "language": user.language, "is_active": user.is_active},
        "demo_mode": True,
    }


@router.post("/auth/otp/request", response_model=OtpRequestResponse)
def api_request_otp(data: OtpRequest):
    req_id, otp = request_otp(data.phone, data.role)
    return OtpRequestResponse(
        request_id=req_id,
        message="Development OTP generated",
        mock_otp=otp if settings.MOCK_OTP else None
    )


@router.post("/auth/otp/verify", response_model=TokenResponse)
def api_verify_otp(data: OtpVerify, db: Session = Depends(get_db)):
    access_token, refresh_token, user, needs_onboarding = verify_otp(db, data.request_id, data.otp)
    user_resp = UserResponse(
        id=user.id,
        phone=user.phone,
        role=user.role,
        name=user.name,
        language=user.language,
        is_active=user.is_active,
        needs_onboarding=needs_onboarding
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_resp
    )


@router.post("/auth/refresh")
def api_refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    new_access, new_refresh = refresh_user_token(db, data.refresh_token)
    return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}


@router.post("/auth/logout")
def api_logout(current_user: User = Depends(get_current_user)):
    return {"message": "Discard tokens on the client. Issued tokens expire on their existing schedule."}


@router.get("/me", response_model=UserResponse)
def api_get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def api_update_me(data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.name is not None:
        current_user.name = data.name
    if data.language is not None:
        current_user.language = data.language
    db.commit()
    db.refresh(current_user)
    return current_user
