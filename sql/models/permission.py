from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Permission(Base):
    """Granular action capability assigned to roles (e.g. 'user:read', 'chat:use')."""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    # Roles that possess this permission via role_permissions table
    roles = relationship(
        "Role", secondary="role_permissions", back_populates="permissions"
    )
