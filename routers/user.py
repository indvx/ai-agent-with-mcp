from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from core.security import SecurityHandler
from service.user import UserService
from schemas.users import UserResponse
from typing import List

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

user_read_permissions = SecurityHandler().has_permissions(["user:read"])
user_delete_permissions = SecurityHandler().has_permissions(["user:delete"])


@router.get(
    "/",
    dependencies=[Depends(user_read_permissions)],
    response_model=List[UserResponse],
)
def get_users(db: Session = Depends(get_db)):
    user_service = UserService(db)
    users = user_service.get_users()
    return users


@router.get(
    "/{user_id}",
    dependencies=[Depends(user_read_permissions)],
    response_model=UserResponse,
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user_service = UserService(db)
    return user_service.get_user(user_id)


@router.delete("/{user_id}", dependencies=[Depends(user_delete_permissions)])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user_service = UserService(db)
    return user_service.delete_user(user_id)
