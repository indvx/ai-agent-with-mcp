from fastapi import FastAPI, Request
from routers import chat, auth, role, user

app = FastAPI()


app.include_router(chat.router)
app.include_router(auth.router)
app.include_router(role.router)
app.include_router(user.router)


@app.get("/")
async def root():
    return {"message": "Welecome to mcp chat"}


@app.get("/health")
async def health_check(request: Request):
    return {"status": "ok"}
