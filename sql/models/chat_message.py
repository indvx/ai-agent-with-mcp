from database import Base
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from typing import Dict, Any
from sqlalchemy.sql import func

class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=None, nullable=True, onupdate=func.now())