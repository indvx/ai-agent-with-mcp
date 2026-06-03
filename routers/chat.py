from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from service.langgraph_service import LanggraphService
from schemas.chat import Chat

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)
limiter = Limiter(key_func=get_remote_address)
service = LanggraphService()


async def generate_stream_data(query: str):
    try:
        await service.initialize()
        graph = service.build_pipeline()
        async for event in graph.astream_events({"question": query}, version="v2"):
            if event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content
    except Exception as e:
        yield f"\n[Error: {e}]"


@router.post("/")
@limiter.limit("5/minute")
async def chat(query: Chat, request: Request):
    await service.initialize()
    graph = service.build_pipeline()

    response = await graph.ainvoke(
        {
            "question": query.query,
        }
    )
    return response


@router.post("/stream")
@limiter.limit("5/minute")
async def chat_stream(query: Chat, request: Request):
    return StreamingResponse(
        generate_stream_data(query.query),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
