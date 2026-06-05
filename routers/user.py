from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from core.security import JWTBearer, has_permissions, has_roles
from service.user import UserService

from schemas.users import UserResponse, UserListResponse

from typing import Any

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=UserListResponse)
def get_users(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    d: Any = Depends(has_permissions(["user:read", "user:manage"])),
):
    user_service = UserService(db)
    users = user_service.get_users(page, limit)
    return users


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int, db: Session = Depends(get_db), d: Any = Depends(JWTBearer())
):
    user_service = UserService(db)
    return user_service.get_user(user_id)


@router.delete("/{user_id}")
def delete_user(
    user_id: int, db: Session = Depends(get_db), d: Any = Depends(has_roles(["admin"]))
):
    user_service = UserService(db)
    return user_service.delete_user(user_id)
