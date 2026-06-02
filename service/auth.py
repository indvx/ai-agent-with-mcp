from fastapi import HTTPException
from sql.crud import (
    users as user_crud,
    role as role_crud,
    refresh_token as refresh_token_crud,
)
from datetime import datetime, timedelta, timezone
import jwt
import uuid
import os
from schemas.auth import RegisterRequest, LoginRequest
from service.base_service import BaseService


class AuthService(BaseService):
    def __init__(self):
        super().__init__()
        self._secret_key = os.getenv("SECRET_KEY")
        self._algorithm = os.getenv("ALGORITHM", "HS256")
        self._access_token_expire_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15)
        )
        self._refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

    def register(self, payload: RegisterRequest):
        existing_user = user_crud.get_user(self.db, payload.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")

        default_role = role_crud.get_default_role(self.db)
        if not default_role:
            raise HTTPException(status_code=500, detail=("Default role missing"))

        user = user_crud.create_user(
            self.db,
            email=payload.email,
            full_name=payload.full_name,
            password_hash=payload.password,
        )

        access_token = self.create_jwt_token(user.id, type="access")
        refresh_data = self.create_jwt_token(user.id, type="refresh")

        refresh_token = refresh_token_crud.create_or_update_refresh_token(
            self.db,
            user_id=user.id,
            jti=refresh_data["jti"],
            token=refresh_data["token"],
            expires_at=refresh_data["expires_at"],
        )
        return {
            "message": "User registered successfully",
            "access_token": access_token,
            "refresh_token": refresh_token.token,
            "token_type": "bearer",
        }

    def login(self, payload: LoginRequest):
        user = user_crud.get_user(self.db, payload.email)
        if not user:
            raise HTTPException(status_code=401, detail=("Invalid credentials"))

        valid_password = user_crud.verify_password(payload.password, user.password_hash)
        if not valid_password:
            raise HTTPException(status_code=401, detail=("Invalid password"))

        if not user.is_active:
            raise HTTPException(status_code=403, detail=("Your account is inactive"))

        if not user.is_verified:
            raise HTTPException(status_code=403, detail=("Verify your account"))

        access_token = self.create_jwt_token(user.id, type="access")
        refresh_data = self.create_jwt_token(user.id, type="refresh")

        refresh_token = refresh_token_crud.create_or_update_refresh_token(
            self.db,
            user_id=user.id,
            jti=refresh_data["jti"],
            token=refresh_data["token"],
            expires_at=refresh_data["expires_at"],
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token.token,
            "token_type": "bearer",
        }

    def refresh_token(self, refresh_token: str):
        payload = self.decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail=("Invalid token type"))

        jti = payload.get("jti")
        ref_token = refresh_token_crud.get_token_by_jti_or_user_id(self.db, jti=jti)
        if not ref_token:
            raise HTTPException(status_code=401, detail=("Token not found"))

        if bool(ref_token.revoked):
            raise HTTPException(status_code=401, detail=("Token is revoked"))

        if refresh_token_crud.is_refresh_token_expired(ref_token):
            raise HTTPException(status_code=401, detail=("Token is expired"))

        access_token = self.create_jwt_token(ref_token.user_id, type="access")
        return {"access_token": access_token, "token_type": "bearer"}

    def logout(self, user_id: int):
        refresh_token = refresh_token_crud.get_token_by_jti_or_user_id(
            self.db, user_id=user_id, revoked=False
        )
        refresh_token.revoked = True
        self.db.commit()
        self.db.refresh(refresh_token)

        return {"message": "Logged out successfully"}

    def create_jwt_token(self, user_id: int, type: str = "access"):
        if type == "access":
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self._access_token_expire_minutes
            )
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=self._refresh_token_expire_days
            )

        jti = str(uuid.uuid4())
        payload = {
            "sub": str(user_id),
            "type": type,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": jti,
        }

        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        if type == "access":
            return token

        return {"token": token, "jti": jti, "expires_at": expire}

    def decode_token(self, token: str):
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail=("Token expired"))

        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail=("Invalid token"))
