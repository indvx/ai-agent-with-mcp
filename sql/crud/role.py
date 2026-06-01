from sql.models.role import Role
from sql.models.users import User
from sql.models.permission import Permission
from sqlalchemy.orm import Session


def get_default_role(db: Session):
    return db.query(Role).filter(Role.is_default == True).first()


def get_role(db: Session, role_id: int):
    return db.query(Role).filter(Role.id == role_id).first()


def get_roles(db: Session):
    roles = db.query(Role).all()
    return roles


def assign_role(db: Session, user_id: int, role_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.id == role_id).first()
    if not user:
        raise ValueError("User not found")

    if not role:
        raise ValueError("Role not found")

    user.roles.append(role)
    db.commit()


def assign_permission(db: Session, role_id: int, permission_id: int):
    role = db.query(Role).filter(Role.id == role_id).first()
    permission = db.query(Permission).filter(Permission.id == permission_id).first()

    if not role:
        raise ValueError("Role not found")

    if not permission:
        raise ValueError("Permission not found")

    role.permissions.append(permission)

    db.commit()
