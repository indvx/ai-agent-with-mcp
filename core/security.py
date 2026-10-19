from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sql.models.users import User
import jwt
import os
from database import get_db
from service.user import UserService

secret_key = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM", "HS256")


class JWTBearer(HTTPBearer):
    """Extracts and verifies the Bearer token from the incoming request Authorization header."""

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials = await super().__call__(request)

        # Make sure the scheme is explicitly 'Bearer'
        if not credentials or credentials.scheme != "Bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication",
            )

        return credentials.credentials


def get_current_user(
    token: str = Depends(JWTBearer()),
    db: Session = Depends(get_db),
):
    """Validates the JWT token and returns the authenticated active user."""
    payload = decode_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    # Use the request's scoped DB session rather than a global session
    user_service = UserService(db)
    try:
        user = user_service.get_user(user_id)
    except Exception:
        user = None

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Block deactivated accounts even if the JWT has not expired yet
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return user


def has_roles(allowed_roles: list[str]):
    """Ensures the caller has at least one of the required roles (e.g. ['admin', 'manager'])."""
    def role_checker(current_user: User = Depends(get_current_user)):
        user_roles = [role.name for role in current_user.roles]
        has_role = any(role in user_roles for role in allowed_roles)

        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )

        return current_user

    return role_checker


def has_permissions(allowed_permissions: list[str]):
    """Ensures the caller has at least one of the required permissions across their roles."""
    def permission_checker(
        current_user: User = Depends(get_current_user),
    ):
        # A user can have multiple roles, so flatten all permissions into one list
        permissions = []
        for role in current_user.roles:
            permissions.extend([p.name for p in role.permissions])

        has_permission = any(
            permission in permissions for permission in allowed_permissions
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )

        return current_user

    return permission_checker


def decode_token(token: str):
    """Decodes and validates JWT token expiration and signature."""
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
