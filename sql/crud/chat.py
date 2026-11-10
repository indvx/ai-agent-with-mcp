import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from sql.models.chat_session import ChatSession
from sql.models.chat_message import ChatMessage
from core.logger import get_logger

logger = get_logger(__name__)


def get_or_create_session(db: Session, session_id: Optional[str] = None, title: Optional[str] = None) -> str:
    """Returns the existing session_id or creates and returns a new session_id."""
    sid = session_id.strip() if session_id and session_id.strip() else str(uuid.uuid4())
    try:
        session_obj = db.query(ChatSession).filter(ChatSession.session_id == sid).first()
        if not session_obj:
            session_obj = ChatSession(session_id=sid, title=title)
            db.add(session_obj)
            db.commit()
            db.refresh(session_obj)
        elif title and not session_obj.title:
            session_obj.title = title
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
        session_obj = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session_obj:
            return []

        records = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_obj.id)
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
    """Persists an individual message to MySQL linked by session foreign key."""
    if not session_id or not content:
        return None

    try:
        session_obj = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session_obj:
            session_obj = ChatSession(session_id=session_id)
            db.add(session_obj)
            db.commit()
            db.refresh(session_obj)

        if role == "user" and not session_obj.title:
            session_obj.title = content[:60]
            db.commit()

        # ChatMessage.session_id is an integer foreign key referencing ChatSession.id
        msg = ChatMessage(session_id=session_obj.id, role=role, content=content)
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg
    except Exception as e:
        logger.error("Failed to save chat message to MySQL: %s", e)
        db.rollback()
        return None


def clear_session_history(db: Session, session_id: str) -> bool:
    """Deletes all messages and session record for a given session."""
    if not session_id:
        return False

    try:
        session_obj = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session_obj:
            return False

        # Delete child messages first to satisfy MySQL foreign key constraint (NO ACTION)
        db.query(ChatMessage).filter(ChatMessage.session_id == session_obj.id).delete()
        db.delete(session_obj)
        db.commit()
        return True
    except Exception as e:
        logger.error("Failed to clear session messages in MySQL: %s", e)
        db.rollback()
        return False


def get_all_sessions(db: Session, limit: int = 50) -> List[dict]:
    """Returns a list of recent sessions with a preview title."""
    try:
        # Join on integer primary/foreign key: ChatMessage.session_id == ChatSession.id
        sessions = (
            db.query(ChatSession)
            .join(ChatMessage, ChatMessage.session_id == ChatSession.id)
            .group_by(ChatSession.id)
            .order_by(ChatSession.id.desc())
            .limit(limit)
            .all()
        )
        result = []
        for s in sessions:
            result.append({
                "session_id": s.session_id,
                "title": s.title,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            })
        return result
    except Exception as e:
        logger.error("Failed to fetch session list from MySQL: %s", e)
        return []
