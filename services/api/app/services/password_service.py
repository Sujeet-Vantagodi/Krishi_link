import hashlib
import hmac
import secrets

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import UserRole
from app.models.user import Buyer, Farmer, PasswordCredential, User
from app.schemas.auth import PasswordLogin, PasswordRegistration


def derive_password(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**15, r=8, p=3, maxmem=64 * 1024**2,
    )


def login_with_password(db: Session, data: PasswordLogin) -> tuple[User, str | None]:
    user = db.query(User).filter_by(phone=data.phone).first()
    credential = db.get(PasswordCredential, user.id) if user else None
    salt, expected = credential.password_hash.split(":") if credential else ("00" * 16, "00" * 64)
    actual = derive_password(data.password.get_secret_value(), bytes.fromhex(salt))
    valid = hmac.compare_digest(actual, bytes.fromhex(expected))
    if not valid or not credential or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid phone number or password")
    return user, credential.contact_email


def register_password_account(db: Session, data: PasswordRegistration) -> tuple[User, str | None]:
    if data.role not in (UserRole.BUYER, UserRole.FARMER):
        raise HTTPException(status_code=403, detail="This role requires an administrator-created account")
    if db.query(User.id).filter_by(phone=data.phone).first():
        raise HTTPException(status_code=409, detail="This phone number already has an account")

    salt = secrets.token_bytes(16)
    digest = derive_password(data.password.get_secret_value(), salt)
    user = User(phone=data.phone, name=data.name.strip(), role=data.role,
                language="kn" if data.role == UserRole.FARMER else "en")
    db.add(user)
    try:
        db.flush()
        db.add(PasswordCredential(user_id=user.id, password_hash=f"{salt.hex()}:{digest.hex()}", contact_email=data.email))
        if data.role == UserRole.BUYER:
            db.add(Buyer(user_id=user.id, business_name=data.business_name or user.name,
                         business_type=data.business_type, address=data.address))
        else:
            db.add(Farmer(user_id=user.id, village=data.village, taluk=data.taluk, land_acres=data.land_acres,
                          default_min_kg=data.min_threshold_kg or settings.DEFAULT_FARMER_THRESHOLD_KG))
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.query(User.id).filter_by(phone=data.phone).first():
            raise HTTPException(status_code=409, detail="This phone number already has an account")
        raise
    return user, data.email
