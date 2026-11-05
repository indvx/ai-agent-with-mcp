from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers import chat

app = FastAPI(
    title="MCP Chat API",
    description="API for MCP Chat application",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


@app.get("/")
async def root():
    """Simple health check endpoint returning welcome message."""
    return {"message": "Welcome to mcp chat"}


@app.get("/health")
async def health_check(request: Request):
    """Liveness probe used by container monitors."""
    return {"status": "ok"}
