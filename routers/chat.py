import uuid
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from core.logger import get_logger
from database import SessionLocal
from sql.crud.chat import (
    get_or_create_session,
    get_recent_messages,
    save_message,
    clear_session_history,
)
from service.langgraph_service import LanggraphService
from schemas.chat import Chat

logger = get_logger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

limiter = Limiter(key_func=get_remote_address)
service = LanggraphService()


async def generate_stream_data(query: str, session_id: Optional[str] = None):
    """Yield model output as tokens arrive from the agent stream."""
    try:
        # Return cached answer immediately if identical/plural-normalized query was previously processed
        cached = service.get_cached_response(query)
        if cached is not None:
            logger.info("[INFO] Streaming cache hit for query: '%s' (0 tokens consumed)", query)
            answer = cached.get("answer", "")
            if answer:
                if session_id:
                    try:
                        db = SessionLocal()
                        try:
                            save_message(db, session_id, "user", query)
                            save_message(db, session_id, "assistant", answer)
                        finally:
                            db.close()
                    except Exception as e:
                        logger.warning("[WARN] Failed to record cached turn in session history: %s", e)
                yield answer
            return

        await service.initialize()
        graph = service.build_pipeline()
        collected_chunks = []

        async for event in graph.astream_events(
            {"question": query, "session_id": session_id}, version="v2"
        ):
            if event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    collected_chunks.append(content)
                    yield content

        full_answer = "".join(collected_chunks)
        if full_answer:
            service.cache_response(
                query,
                {
                    "answer": full_answer,
                    "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                    "tool_calls": [],
                },
            )
    except Exception as e:
        logger.error("[ERROR] Stream generation error: %s", e)
        yield f"\n[Error: {e}]"


@router.post("/")
@limiter.limit("5/minute")
async def chat(query: Chat, request: Request):
    """Run the agent workflow and return the completed response."""
    db = SessionLocal()
    try:
        sid = get_or_create_session(db, query.session_id)
    except Exception as e:
        logger.warning("[WARN] Failed to resolve session in MySQL: %s", e)
        sid = str(uuid.uuid4())
    finally:
        db.close()

    # Return cached response if query already answered within TTL window
    cached = service.get_cached_response(query.query)
    if cached is not None:
        logger.info("[INFO] Cache hit for query: '%s' (0 tokens consumed)", query.query)
        try:
            db = SessionLocal()
            try:
                save_message(db, sid, "user", query.query)
                save_message(db, sid, "assistant", cached.get("answer", ""))
            finally:
                db.close()
        except Exception as e:
            logger.warning("[WARN] Failed to record cached turn in session history: %s", e)
        return {**cached, "session_id": sid}

    await service.initialize()
    graph = service.build_pipeline()

    response = await graph.ainvoke(
        {
            "question": query.query,
            "session_id": sid,
        }
    )
    service.cache_response(query.query, response)
    return {**response, "session_id": sid}


@router.post("/stream")
@limiter.limit("5/minute")
async def chat_stream(query: Chat, request: Request):
    """Stream the agent response as server-sent events."""
    db = SessionLocal()
    try:
        sid = get_or_create_session(db, query.session_id)
    except Exception as e:
        logger.warning("[WARN] Failed to resolve session in MySQL: %s", e)
        sid = str(uuid.uuid4())
    finally:
        db.close()

    return StreamingResponse(
        generate_stream_data(query.query, sid),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Retrieves recent conversation message history for a given session."""
    try:
        db = SessionLocal()
        try:
            messages = get_recent_messages(db, session_id, limit=20)
            return {
                "session_id": session_id,
                "messages": [
                    {"role": m.type, "content": m.content}
                    for m in messages
                ],
            }
        finally:
            db.close()
    except Exception as e:
        logger.error("[ERROR] Failed to fetch session history: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch session history")


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clears conversation messages for a given session."""
    try:
        db = SessionLocal()
        try:
            success = clear_session_history(db, session_id)
            return {"session_id": session_id, "cleared": success}
        finally:
            db.close()
    except Exception as e:
        logger.error("[ERROR] Failed to clear session: %s", e)
        raise HTTPException(status_code=500, detail="Failed to clear session")
