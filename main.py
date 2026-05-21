from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.chat import router as chat_router
from app.routes.mood import router as mood_router

app = FastAPI(
    title="MindEase API",
    description="Mental Health First Responder Chatbot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
app.include_router(mood_router, prefix="/api/v1", tags=["Mood"])

@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"status": "MindEase API is running 🧠"}
