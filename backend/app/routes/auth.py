from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database.orm import orm_create_user, orm_get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = "analyst"


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserRegistration):
    if user.role not in {"admin", "analyst", "viewer"}:
        raise HTTPException(status_code=400, detail="Invalid user role")
    if orm_get_user_by_email(user.email):
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    try:
        created = orm_create_user(user.email, hash_password(user.password), user.role)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to create user") from exc
    return {"id": created.id, "email": created.email, "role": created.role, "is_active": created.is_active}


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = orm_get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": create_access_token(user.email, user.role),
        "token_type": "bearer",
        "role": user.role,
    }


@router.get("/me")
def current_user(current_user=Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "role": current_user["role"],
        "is_active": current_user["is_active"],
    }
