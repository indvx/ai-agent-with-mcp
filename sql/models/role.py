from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base
from sql.models.role_permission import RolePermission
from sql.models.permission import Permission
from sql.models.user_roles import UserRoles


class Role(Base):
    """System role grouping users and granted permissions."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)

    # Users assigned to this role via user_roles table
    users = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        uselist=False,
    )

    # Eagerly load permissions so auth checks don't fire secondary SQL queries
    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="joined",
    )
