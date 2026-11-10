
from database import Base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from .chat_message import ChatMessage
from datetime import datetime, UTC

class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    session_id = Column(String(255), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now(UTC))
    messages = relationship("ChatMessage", back_populates="chat_session",cascade="all, delete-orphan")