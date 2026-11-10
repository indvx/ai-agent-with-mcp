import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from sql.models.chat_session import ChatSession
from sql.models.chat_message import ChatMessage
from core.logger import get_logger

logger = get_logger(__name__)


def get_or_create_session(db: Session, session_id: Optional[str] = None) -> str:
    """Returns the existing session_id or creates and returns a new session_id."""
    sid = session_id.strip() if session_id and session_id.strip() else str(uuid.uuid4())
    try:
        session_obj = db.query(ChatSession).filter(ChatSession.session_id == sid).first()
        if not session_obj:
            session_obj = ChatSession(session_id=sid)
            db.add(session_obj)
            db.commit()
    except Exception as e:
        logger.warning("Failed to get_or_create_session in MySQL: %s", e)
        db.rollback()
    return sid


def get_recent_messages(db: Session, session_id: str, limit: int = 6) -> List[BaseMessage]:
    """Retrieves the last N messages for a session as LangChain message instances."""
    if not session_id:
        return []

    try:
        records = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.desc())
            .limit(limit)
            .all()
        )
        records.reverse()

        messages: List[BaseMessage] = []
        for rec in records:
            if rec.role == "user":
                messages.append(HumanMessage(content=rec.content))
            elif rec.role == "assistant":
                messages.append(AIMessage(content=rec.content))
        return messages
    except Exception as e:
        logger.warning("Failed to load chat history from MySQL: %s", e)
        return []


def save_message(db: Session, session_id: str, role: str, content: str) -> Optional[ChatMessage]:
    """Persists an individual message to MySQL."""
    if not session_id or not content:
        return None

    try:
        get_or_create_session(db, session_id)
        msg = ChatMessage(session_id=session_id, role=role, content=content)
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg
    except Exception as e:
        logger.error("Failed to save chat message to MySQL: %s", e)
        db.rollback()
        return None


def clear_session_history(db: Session, session_id: str) -> bool:
    """Deletes all messages associated with a session."""
    if not session_id:
        return False

    try:
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        db.commit()
        return True
    except Exception as e:
        logger.error("Failed to clear session messages in MySQL: %s", e)
        db.rollback()
        return False
