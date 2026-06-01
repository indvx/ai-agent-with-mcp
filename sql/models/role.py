from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base
from sql.models.role_permission import RolePermission
from sql.models.permission import Permission
from sql.models.user_roles import UserRoles


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    users = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        uselist=False,
    )

    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="joined",
    )
