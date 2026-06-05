from pydantic import BaseModel, EmailStr
from typing import Any


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    created_at: Any
    updated_at: Any
    class ConfigDict:
        from_attributes = True
