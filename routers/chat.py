from fastapi import APIRouter, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from service.langgraph_service import LanggraphService
from schemas.chat import Chat
from core.security import SecurityHandler

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)
limiter = Limiter(key_func=get_remote_address)
service = LanggraphService()


@router.post("/", dependencies=[Depends(SecurityHandler().has_permissions(["chat:use"]))])
@limiter.limit("5/minute")
async def chat(query: Chat, request: Request, ):
    await service.initialize()
    graph = service.build_pipeline()

    response = await graph.ainvoke(
        {
            "question": query.query,
        }
    )
    return response
