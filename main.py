from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from routers import chat
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="MCP Chat API",
    description="API for MCP Chat application",
    version="1.0.0",
)


app.include_router(chat.router)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*")
if allowed_origins == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in allowed_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/docs", include_in_schema=False)
async def swagger_ui_html(req: Request) -> HTMLResponse:
    root_path = req.scope.get("root_path", "").rstrip("/")
    openapi_url = root_path + app.openapi_url
    oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url
    if oauth2_redirect_url:
        oauth2_redirect_url = root_path + oauth2_redirect_url
    swagger_favicon_url = f"{root_path}/static/logo.svg" if root_path else "/static/logo.svg"
    print("swagger_favicon_url", swagger_favicon_url)
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=oauth2_redirect_url,
        init_oauth=app.swagger_ui_init_oauth,
        swagger_favicon_url=swagger_favicon_url,
        swagger_ui_parameters=app.swagger_ui_parameters,
    )

@app.get("/")
async def root():
    return {"message": "Welecome to mcp chat"}


@app.get("/health")
async def health_check(request: Request):
    return {"status": "ok"}
