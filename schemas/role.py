from pydantic import BaseModel
from typing import List


class PermissionResponse(BaseModel):
    id: int
    name: str

    class ConfigDict:
        from_attributes = True


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str | None

    permissions: List[PermissionResponse] = []

    class ConfigDict:
        from_attributes = True
