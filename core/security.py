from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sql.models.users import User
import jwt
import os
from database import get_db
from service.user import UserService

db = next(get_db())
secret_key = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM", "HS256")
user_service = UserService(db)


class JWTBearer(HTTPBearer):

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request):

        credentials = await super().__call__(request)

        if not credentials or credentials.scheme != "Bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=("Invalid authentication"),
            )

        return credentials.credentials


def get_current_user(token: str = Depends(JWTBearer())):

    payload = decode_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=("User not found")
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=("Inactive user")
        )
    return user


def has_roles(allowed_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        user_roles = [role.name for role in (current_user.roles)]
        has_role = any(role in user_roles for role in (allowed_roles))

        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=("Permission denied")
            )

        return current_user

    return role_checker


def has_permissions(allowed_permissions: list[str]):
    def permission_checker(
        current_user: User = Depends(get_current_user),
    ):

        permissions = []
        for role in current_user.roles:
            permissions.extend([p.name for p in (role.permissions)])

        has_permission = any(
            permission in permissions for permission in (allowed_permissions)
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=("Permission denied")
            )

        return current_user

    return permission_checker


def decode_token(token: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
