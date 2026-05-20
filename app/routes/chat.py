from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.gemini_service import get_ai_response
from app.services.alert_service import send_crisis_alert
import sqlite3

router = APIRouter()

def save_chat_message(session_id: str, role: str, content: str):
    conn = sqlite3.connect("mindease.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute(
        "INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    conn.commit()
    conn.close()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = get_ai_response(request.message, request.history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

    save_chat_message(request.session_id, "user", request.message)
    save_chat_message(request.session_id, "assistant", result["reply"])

    alert_sent = False
    emergency_contact_recommended = request.emergency_contact is None
    emergency_contact_message = None

    if result["is_crisis"] and request.emergency_contact:
        alert_sent = await send_crisis_alert(
            chat_id=request.emergency_contact.telegram_chat_id,
            contact_name=request.emergency_contact.name,
            session_id=request.session_id,
        )
    elif result["is_crisis"]:
        emergency_contact_message = (
            "No Telegram alert was sent because no trusted contact was added. "
            "MindEase works without one, but adding a contact is strongly recommended for crisis moments."
        )
        result["reply"] = (
            f"{result['reply']} Also, I could not alert anyone because no trusted Telegram contact is set. "
            "If you can, please add one when you feel able."
        )
    elif emergency_contact_recommended:
        emergency_contact_message = (
            "Optional but recommended: add one trusted Telegram contact so MindEase can alert them during a crisis."
        )

    return ChatResponse(
        reply=result["reply"],
        emotion_scores=result["emotion_scores"],
        is_crisis=result["is_crisis"],
        crisis_resources=result["crisis_resources"],
        session_id=request.session_id,
        alert_sent=alert_sent,
        emergency_contact_recommended=emergency_contact_recommended,
        emergency_contact_message=emergency_contact_message,
    )
