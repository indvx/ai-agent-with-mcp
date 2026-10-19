from sqlalchemy import Column, ForeignKey, Integer, ForeignKey
from database import Base

class UserRoles(Base):
    """Bridge table associating users with their assigned roles."""
    __tablename__ = "user_roles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))
