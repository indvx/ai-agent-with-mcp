from database import SessionLocal
from sql.model.role import Role
from sql.model.permission import Permission
from sql.model.users import User
from core.security import hash_password

db = SessionLocal()


permissions = [
    "user:create",
    "user:read",
    "user:update",
    "user:delete",
    "role:manage",
    "permission:manage",
    "chat:use",
]
role_names = [
    "admin",
    "manager",
    "user"
]


def seed_permissions():
    for permission_name in permissions:
        permission = (
            db.query(Permission).filter(Permission.name == permission_name).first()
        )

        if not permission:
            permission = Permission(name=permission_name)
            db.add(permission)

    db.commit()


def seed_roles():
    for role_name in role_names:
        role = db.query(Role).filter(Role.name == role_name).first()

        if not role:
            role = Role(name=role_name)
            db.add(role)
    db.commit()


def assign_permissions():
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    manager_role = db.query(Role).filter(Role.name == "manager").first()
    user_role = db.query(Role).filter(Role.name == "user").first()
    all_permissions = db.query(Permission).all()
    admin_role.permissions = all_permissions
    manager_permissions = (
        db.query(Permission)
        .filter(Permission.name.in_(["user:read", "user:update"]))
        .all()
    )

    manager_role.permissions = manager_permissions
    user_permissions = db.query(Permission).filter(Permission.name == "user:read").all()
    user_role.permissions = user_permissions
    db.commit()


def create_admin():
    admin = db.query(User).filter(User.email == "admin@test.com").first()
    if admin:
        return

    admin_role = db.query(Role).filter(Role.name == "admin").first()
    admin = User(
        full_name="Admin",
        email="admin@test.com",
        password_hash=(hash_password("Admin@123")),
        is_active=True,
        is_verified=True,
    )

    admin.roles.append(admin_role)
    db.add(admin)
    db.commit()

    print("Admin created")


if __name__ == "__main__":
    seed_permissions()
    seed_roles()
    assign_permissions()
    create_admin()
    print("Seeding completed")
