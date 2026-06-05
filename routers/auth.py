from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    LoginResponse,
    RefreshTokenResponse,
    MessageResponse,
)
from service.auth import AuthService
from core.security import SecurityHandler
from sql.models.users import User
from schemas.users import UserResponse

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@router.post("/register", status_code=201, response_model=MessageResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.register(payload=payload)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.login(payload=payload)


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.refresh_token(refresh_token=payload.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    current_user: User = Depends(SecurityHandler().get_current_user),
    db: Session = Depends(get_db),
):
    auth_service = AuthService(db)
    return auth_service.logout(user_id=current_user.id)


@router.get("/me", response_model=UserResponse)
def me(
    current_user: User = Depends(SecurityHandler().get_current_user),
    db: Session = Depends(get_db),
):
    return current_user
