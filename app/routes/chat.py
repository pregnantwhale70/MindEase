from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatMessage, ChatRequest, ChatResponse
from app.routes.mood import (
    build_emotional_state,
    get_breathing_pattern_for_score,
    get_stress_color,
)
from app.services.gemini_service import get_ai_response, update_conversation_summary
from app.services.alert_service import send_crisis_alert
import json
import sqlite3

router = APIRouter()

def get_db():
    conn = sqlite3.connect("mindease.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_chat_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def init_emotion_scores_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS emotion_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            anxiety_score INTEGER,
            stress_score INTEGER,
            emotions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def init_chat_summary_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_summaries (
            session_id TEXT PRIMARY KEY,
            summary TEXT NOT NULL DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_chat_history(session_id: str, limit: int = 12) -> list[ChatMessage]:
    conn = get_db()
    rows = conn.execute("""
        SELECT role, content
        FROM chat_history
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (session_id, limit)).fetchall()
    conn.close()

    return [
        ChatMessage(role=row["role"], content=row["content"])
        for row in reversed(rows)
    ]

def save_chat_message(session_id: str, role: str, content: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    conn.commit()
    conn.close()

def save_emotion_scores(session_id: str, emotion_scores):
    conn = get_db()
    conn.execute(
        """
        INSERT INTO emotion_scores (session_id, anxiety_score, stress_score, emotions)
        VALUES (?, ?, ?, ?)
        """,
        (
            session_id,
            emotion_scores.anxiety_score,
            emotion_scores.stress_score,
            json.dumps(emotion_scores.emotions),
        )
    )
    conn.commit()
    conn.close()

def get_chat_summary(session_id: str) -> str:
    conn = get_db()
    row = conn.execute(
        "SELECT summary FROM chat_summaries WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    conn.close()
    return row["summary"] if row and row["summary"] else ""

def save_chat_summary(session_id: str, summary: str):
    conn = get_db()
    conn.execute(
        """
        INSERT INTO chat_summaries (session_id, summary, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(session_id) DO UPDATE SET
            summary = excluded.summary,
            updated_at = CURRENT_TIMESTAMP
        """,
        (session_id, summary),
    )
    conn.commit()
    conn.close()

def get_request_history(request: ChatRequest) -> list[ChatMessage]:
    return [
        message
        for message in request.history
        if message.role in {"user", "assistant"} and message.content.strip()
    ]

init_chat_table()
init_emotion_scores_table()
init_chat_summary_table()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    request_history = get_request_history(request)
    history = request_history or get_chat_history(request.session_id)
    session_summary = get_chat_summary(request.session_id)

    try:
        result = get_ai_response(request.message, history, session_summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

    save_chat_message(request.session_id, "user", request.message)

    alert_sent = False
    emergency_contact_recommended = request.emergency_contact is None
    emergency_contact_message = None

    if result["is_crisis"] and request.emergency_contact:
        alert_sent = await send_crisis_alert(
            chat_id=request.emergency_contact.telegram_chat_id,
            contact_name=request.emergency_contact.name,
            session_id=request.session_id,
            user_name=request.user_name,
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

    save_chat_message(request.session_id, "assistant", result["reply"])
    save_emotion_scores(request.session_id, result["emotion_scores"])
    stress_score = result["emotion_scores"].stress_score
    anxiety_score = result["emotion_scores"].anxiety_score
    emotions = result["emotion_scores"].emotions
    stress_load_percent = round(((stress_score + anxiety_score) / 2) * 10)
    updated_summary = update_conversation_summary(
        session_summary,
        [
            *history,
            ChatMessage(role="user", content=request.message),
            ChatMessage(role="assistant", content=result["reply"]),
        ],
    )
    save_chat_summary(request.session_id, updated_summary)

    return ChatResponse(
        reply=result["reply"],
        emotion_scores=result["emotion_scores"],
        insights=result.get("insights", []),
        suggestions=result.get("suggestions", []),
        is_crisis=result["is_crisis"],
        crisis_resources=result["crisis_resources"],
        session_id=request.session_id,
        alert_sent=alert_sent,
        emergency_contact_recommended=emergency_contact_recommended,
        emergency_contact_message=emergency_contact_message,
        breathing_pattern=get_breathing_pattern_for_score(stress_score),
        emotional_state=build_emotional_state(anxiety_score, stress_score, emotions),
        stress_load_percent=stress_load_percent,
        stress_color=get_stress_color(stress_score),
    )
