from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, auth, role, user

app = FastAPI(
    title="MCP Chat API",
    description="API for MCP Chat application",
    version="1.0.0",
)

# Enable CORS so frontend web apps can call the API without browser errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules for chat, authentication, roles, and users
app.include_router(chat.router)
app.include_router(auth.router)
app.include_router(role.router)
app.include_router(user.router)


@app.get("/")
async def root():
    """Simple health check endpoint returning welcome message."""
    return {"message": "Welcome to mcp chat"}


@app.get("/health")
async def health_check(request: Request):
    """Liveness probe used by Docker and container monitors."""
    return {"status": "ok"}
