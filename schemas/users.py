from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo
from typing import Any, List, Optional


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    created_at: Any
    updated_at: Any

    class ConfigDict:
        from_attributes = True


class Meta(BaseModel):
    current_items: Optional[int] = None
    limit: Optional[int] = None
    page: Optional[int] = None
    total_items: Optional[int] = None


class UserListResponse(BaseModel):
    users: Optional[List[UserResponse]] = []
    meta: Optional[Meta]
