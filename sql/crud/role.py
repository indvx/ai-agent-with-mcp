from sql.models.role import Role
from sql.models.users import User
from sql.models.permission import Permission
from sqlalchemy.orm import Session


def get_default_role(db: Session):
    """Retrieves the default role assigned to newly registered users."""
    return db.query(Role).filter(Role.is_default == True).first()


def get_role(db: Session, role_id: int):
    """Retrieves a role by its primary key ID."""
    return db.query(Role).filter(Role.id == role_id).first()


def get_roles(db: Session):
    """Returns all roles configured in the database."""
    roles = db.query(Role).all()
    return roles


def assign_role(db: Session, user_id: int, role_id: int):
    """Links a role to a user record in the user_roles table."""
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.id == role_id).first()
    if not user:
        raise ValueError("User not found")

    if not role:
        raise ValueError("Role not found")

    user.roles.append(role)
    db.commit()


def assign_permission(db: Session, role_id: int, permission_id: int):
    """Links a permission to a role in the role_permissions table."""
    role = db.query(Role).filter(Role.id == role_id).first()
    permission = db.query(Permission).filter(Permission.id == permission_id).first()

    if not role:
        raise ValueError("Role not found")

    if not permission:
        raise ValueError("Permission not found")

    role.permissions.append(permission)

    db.commit()
