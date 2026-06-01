from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sql.models.users import User
import jwt
import os
from database import get_db
from service.user import UserService


class JWTBearer(HTTPBearer):

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request):

        credentials = await super().__call__(request)

        if not credentials or credentials.scheme != "Bearer":
            raise HTTPException(status_code=401, detail=("Invalid authentication"))

        return credentials.credentials


class SecurityHandler:
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY")
        self.algorithm = os.getenv("ALGORITHM", "HS256")
        self._user_service = UserService()

    def get_current_user(
        self, token: str = Depends(JWTBearer()), db: Session = Depends(get_db)
    ):

        payload = self.decode_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = self._user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=("User not found"))

        if not user.is_active:
            raise HTTPException(status_code=403, detail=("Inactive user"))

        return user

    def has_roles(self, allowed_roles: list[str]):
        def role_checker(current_user: User = Depends(self.get_current_user)):
            user_roles = [role.name for role in (current_user.roles)]
            has_role = any(role in user_roles for role in (allowed_roles))

            if not has_role:
                raise HTTPException(status_code=403, detail=("Permission denied"))

            return current_user

        return role_checker

    def has_permissions(self, allowed_permissions: list[str]):
        def permission_checker(
            current_user: User = Depends(self.get_current_user),
        ):

            permissions = []
            for role in current_user.roles:
                permissions.extend([p.name for p in (role.permissions)])

            has_permission = any(
                permission in permissions for permission in (allowed_permissions)
            )

            if not has_permission:
                raise HTTPException(status_code=403, detail=("Permission denied"))

            return current_user

        return permission_checker

    def decode_token(self, token: str):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
            )

        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
