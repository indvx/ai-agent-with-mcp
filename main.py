from fastapi import FastAPI, Request
from pydantic import BaseModel
from routers import chat

app = FastAPI()


app.include_router(chat.router)


@app.get("/")
async def root():
    return {"message": "Welecome to mcp chat"}


@app.get("/health")
async def health_check(request: Request):
    return {"status": "ok"}
