from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routes import chat, mood

app = FastAPI(title="MindEase API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(mood.router, prefix="/api/v1", tags=["Mood"])

@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.app_env}
