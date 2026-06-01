from sql.crud import role as role_crud
from service.base_service import BaseService


class RoleService(BaseService):
    def __init__(self):
        super().__init__()

    def get_roles(self):
        return role_crud.get_roles(self.db)

    def assign_role(self, user_id: int, role_id: int):
        return role_crud.assign_role(self.db, user_id, role_id)

    def assign_permission(self, role_id: int, permission_id: int):
        return role_crud.assign_permission(self.db, role_id, permission_id)
