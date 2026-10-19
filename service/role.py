from sql.crud import role as role_crud


class RoleService:
    """Manages role assignments and permission grants."""

    def __init__(self, db):
        self.db = db

    def __db_close(self):
        self.db.close()

    def get_roles(self):
        """Returns all configured system roles."""
        return role_crud.get_roles(self.db)

    def assign_role(self, user_id: int, role_id: int):
        """Associates a role with a user account."""
        return role_crud.assign_role(self.db, user_id, role_id)

    def assign_permission(self, role_id: int, permission_id: int):
        """Grants a specific permission to a role."""
        return role_crud.assign_permission(self.db, role_id, permission_id)
