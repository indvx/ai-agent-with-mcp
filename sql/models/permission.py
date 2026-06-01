from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    roles = relationship(
        "Role", secondary="role_permissions", back_populates="permissions"
    )
