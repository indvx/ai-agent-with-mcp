from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from core.security import SecurityHandler
from schemas.role import RoleResponse
from typing import List
from service.role import RoleService

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
    responses={404: {"description": "Not found"}},
)

role_service = RoleService()


@router.get("/", dependencies=[Depends(SecurityHandler().has_permissions(["role:manage"]))])
def get_roles():
    return role_service.get_roles()


@router.post("/assign", dependencies=[Depends(SecurityHandler().has_permissions(["role:manage"]))])
def assign_role(user_id: int, role_id: int):
    role_service.assign_role(user_id, role_id)
    return {"message": "Role assigned successfully"}


@router.post("/permission", dependencies=[Depends(SecurityHandler().has_permissions(["role:manage"]))])
def assign_permission(role_id: int, permission_id: int):
    role_service.assign_permission(role_id, permission_id)
    return {"message": "Permission assigned successfully"}
