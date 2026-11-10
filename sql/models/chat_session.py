
from database import Base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .chat_message import ChatMessage

class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    session_id = Column(String(255), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=None, nullable=True, onupdate=func.now())
    messages = relationship("ChatMessage", back_populates="chat_session",cascade="all, delete-orphan")