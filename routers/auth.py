from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.auth import LoginRequest, RegisterRequest, RefreshTokenRequest
from service.auth import AuthService
from core.security import SecurityHandler
from sql.model.users import User
from schemas.users import UserResponse

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)
auth_service = AuthService()
auth_handler = AuthService()

@router.post("/register")
def register(payload: RegisterRequest):
    return auth_service.register(payload=payload)


@router.post("/login")
def login(payload: LoginRequest):
    return auth_service.login(payload=payload)


@router.post("/refresh")
def refresh_token(payload: RefreshTokenRequest):
    return auth_service.refresh_token(refresh_token=payload.refresh_token)


@router.post("/logout")
def logout(current_user: User = Depends(SecurityHandler().get_current_user)
):
    return auth_service.logout(user_id=current_user.id)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(SecurityHandler().get_current_user)):
    return current_user