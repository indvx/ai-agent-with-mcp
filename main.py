from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from core.config import settings
from core.logger import setup_logging, get_logger
from routers import chat

# Configure application logging
setup_logging()
logger = get_logger(__name__)


app = FastAPI(
    title="MCP Chat API",
    description="API for MCP Chat application",
    version="1.0.0",
    lifespan=lifespan,
)

allow_all_origins = "*" in settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Serves the default chat HTML interface."""
    index_file = STATIC_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return {"message": "Welcome to mcp chat"}


@app.get("/health")
async def health_check(request: Request):
    """Liveness probe used by container monitors."""
    return {"status": "ok"}
