from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from routers import chat, auth, role, user

app = FastAPI(
    title="MCP Chat API",
    description="API for MCP Chat application",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)


app.include_router(chat.router)
app.include_router(auth.router)
app.include_router(role.router)
app.include_router(user.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/docs", include_in_schema=False)
async def swagger_ui_html(req: Request) -> HTMLResponse:
    root_path = req.scope.get("root_path", "").rstrip("/")
    openapi_url = root_path + app.openapi_url
    oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url
    if oauth2_redirect_url:
        oauth2_redirect_url = root_path + oauth2_redirect_url
    swagger_favicon_url = f"{root_path}/static/logo.svg" if root_path else "/static/logo.svg"
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
