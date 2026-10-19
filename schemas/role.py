from pydantic import BaseModel
from typing import List


class PermissionResponse(BaseModel):
    """Granular permission record returned in role metadata."""
    id: int
    name: str

    class ConfigDict:
        from_attributes = True


class RoleResponse(BaseModel):
    """Role definition including its assigned permission list."""
    id: int
    name: str
    description: str | None

    permissions: List[PermissionResponse] = []

    class ConfigDict:
        from_attributes = True
