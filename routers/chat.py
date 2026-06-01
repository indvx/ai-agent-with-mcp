from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from service.langgraph_service import LanggraphService
from schemas.chat import Chat

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
service = LanggraphService()


@router.post("/chat")
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
