
from database import Base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    session_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=None, nullable=True, onupdate=func.now())
    