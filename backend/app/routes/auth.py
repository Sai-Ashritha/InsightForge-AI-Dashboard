from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database.orm import (
    orm_activate_user,
    orm_create_user,
    orm_get_user_by_email,
    orm_save_otp,
    orm_update_password,
    orm_verify_otp,
)
from app.services.email_service import generate_otp, otp_expiry, send_otp_email

router = APIRouter(prefix="/auth", tags=["auth"])

# ── Pydantic schemas ──────────────────────────────────────────────────────────

class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str | None = None
    confirm_password: str | None = None
    role: str = "analyst"


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    code: str


class ResendOTPRequest(BaseModel):
    email: EmailStr
    purpose: str = "verify"   # 'verify' | 'reset'


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str = Field(min_length=6)
    confirm_password: str


# ── Register ─────────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserRegistration):
    if user.role not in {"admin", "analyst", "viewer"}:
        raise HTTPException(status_code=400, detail="Invalid user role")

    # Validate confirm_password if provided
    if user.confirm_password is not None and user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    if orm_get_user_by_email(user.email):
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    try:
        created = orm_create_user(
            email=user.email,
            hashed_password=hash_password(user.password),
            role=user.role,
            full_name=user.full_name,
            is_verified=False,   # requires OTP verification
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to create user") from exc

    # Generate + send OTP
    code = generate_otp()
    expires = otp_expiry()
    orm_save_otp(user.email, code, "verify", expires)
    success, is_real_smtp = send_otp_email(user.email, code, "verify")

    return {
        "id": created.id,
        "email": created.email,
        "full_name": created.full_name,
        "role": created.role,
        "is_verified": created.is_verified,
        "verification_required": True,
        "email_sent": is_real_smtp,
    }


# ── Verify OTP (email verification) ──────────────────────────────────────────

@router.post("/verify-otp")
def verify_otp(payload: OTPVerifyRequest):
    user = orm_get_user_by_email(payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not orm_verify_otp(payload.email, payload.code, "verify"):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    orm_activate_user(payload.email)

    # Auto-login after verification
    token = create_access_token(user.email, user.role)
    return {
        "message": "Email verified successfully!",
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
    }


# ── Resend OTP ────────────────────────────────────────────────────────────────

@router.post("/resend-otp")
def resend_otp(payload: ResendOTPRequest):
    user = orm_get_user_by_email(payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.purpose == "verify" and user.is_verified:
        raise HTTPException(status_code=400, detail="Email is already verified")

    code = generate_otp()
    expires = otp_expiry()
    orm_save_otp(payload.email, code, payload.purpose, expires)
    success, is_real_smtp = send_otp_email(payload.email, code, payload.purpose)

    return {
        "message": "Verification code resent",
        "email_sent": is_real_smtp,
    }


# ── Login (JWT token) ─────────────────────────────────────────────────────────

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = orm_get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # If account exists but OTP not verified, prompt verification
    if not user.is_verified:
        # Re-send OTP so they can verify
        code = generate_otp()
        expires = otp_expiry()
        orm_save_otp(user.email, code, "verify", expires)
        success, is_real_smtp = send_otp_email(user.email, code, "verify")
        raise HTTPException(
            status_code=403,
            detail="Email not verified. A new verification code has been sent to your email.",
            headers={"X-Verify-Email": user.email},
        )

    return {
        "access_token": create_access_token(user.email, user.role),
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name,
    }


# ── Forgot Password ──────────────────────────────────────────────────────────

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    user = orm_get_user_by_email(payload.email)
    # Always return 200 to avoid user enumeration
    if not user:
        return {"message": "If this email is registered, a reset code has been sent."}

    code = generate_otp()
    expires = otp_expiry()
    orm_save_otp(payload.email, code, "reset", expires)
    success, is_real_smtp = send_otp_email(payload.email, code, "reset")

    return {
        "message": "Password reset code sent to your email",
        "email_sent": is_real_smtp,
    }



# ── Reset Password ────────────────────────────────────────────────────────────

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest):
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = orm_get_user_by_email(payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not orm_verify_otp(payload.email, payload.code, "reset"):
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")

    orm_update_password(payload.email, hash_password(payload.new_password))

    return {"message": "Password reset successfully. You can now sign in."}


# ── Me (current user) ─────────────────────────────────────────────────────────

@router.get("/me")
def current_user_info(current_user=Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "role": current_user["role"],
        "is_active": current_user["is_active"],
    }
