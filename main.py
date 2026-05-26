from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.websockets import WebSocket
from pydantic import BaseModel
from enum import Enum
from langgraph_service import LanggraphService
from slowapi import Limiter
from slowapi.util import get_remote_address

app = FastAPI()

class Chat(BaseModel):
    query: str
    
service = LanggraphService()
limiter = Limiter(key_func=get_remote_address)

@app.get("/")
async def root():
    return {"message": "Welecome to mcp chat"}

@app.get("/health")
async def health_check(request: Request):
    return {"status": "ok"}


@app.post("/chat")
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
