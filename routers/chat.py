from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from core.logger import get_logger
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


async def generate_stream_data(query: str):
    """Yield model output as tokens arrive from the agent stream."""
    try:
        # Return cached answer immediately if identical query was previously processed
        cached = service.get_cached_response(query)
        if cached is not None:
            logger.info("Streaming cache hit for query: '%s' (0 tokens consumed)", query)
            answer = cached.get("answer", "")
            if answer:
                yield answer
            return

        await service.initialize()
        graph = service.build_pipeline()
        collected_chunks = []

        async for event in graph.astream_events({"question": query}, version="v2"):
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
        logger.error("Stream generation error: %s", e)
        yield f"\n[Error: {e}]"


@router.post("/")
@limiter.limit("5/minute")
async def chat(query: Chat, request: Request):
    """Run the agent workflow and return the completed response."""
    # Return cached response if query already answered within TTL window
    cached = service.get_cached_response(query.query)
    if cached is not None:
        logger.info("Cache hit for query: '%s' (0 tokens consumed)", query.query)
        return cached

    await service.initialize()
    graph = service.build_pipeline()

    response = await graph.ainvoke(
        {
            "question": query.query,
        }
    )
    service.cache_response(query.query, response)
    return response


@router.post("/stream")
@limiter.limit("5/minute")
async def chat_stream(query: Chat, request: Request):
    """Stream the agent response as server-sent events."""
    return StreamingResponse(
        generate_stream_data(query.query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
