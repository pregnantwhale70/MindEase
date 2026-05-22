from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import json
import re
import sqlite3

router = APIRouter()

class MoodEntry(BaseModel):
    session_id: str
    score: int
    note: str = ""

class MoodResponse(BaseModel):
    id: int
    session_id: str
    score: int
    note: str
    date: str

class AnalyticsResponse(BaseModel):
    dates: List[str]
    scores: List[int]
    average: float
    highest: int
    lowest: int

class InsightsResponse(BaseModel):
    insights: List[str]
    suggestions: List[str]

def get_db():
    conn = sqlite3.connect("mindease.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_mood_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS moods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (date('now'))
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

init_mood_table()
init_emotion_scores_table()

@router.post("/mood", response_model=MoodResponse)
def save_mood(entry: MoodEntry):
    if not 1 <= entry.score <= 10:
        raise HTTPException(status_code=400, detail="Score must be between 1 and 10")

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO moods (session_id, score, note) VALUES (?, ?, ?)",
        (entry.session_id, entry.score, entry.note)
    )
    conn.commit()
    row_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM moods WHERE id = ?", (row_id,)).fetchone()
    conn.close()

    return MoodResponse(
        id=row["id"],
        session_id=row["session_id"],
        score=row["score"],
        note=row["note"],
        date=row["created_at"]
    )

@router.get("/analytics/{session_id}", response_model=AnalyticsResponse)
def get_analytics(session_id: str, days: int = 7):
    conn = get_db()
    rows = conn.execute("""
        SELECT score, created_at
        FROM moods
        WHERE session_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (session_id, days)).fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No mood data found")

    scores = [r["score"] for r in rows]
    dates  = [r["created_at"] for r in rows]

    return AnalyticsResponse(
        dates=list(reversed(dates)),
        scores=list(reversed(scores)),
        average=round(sum(scores) / len(scores), 1),
        highest=max(scores),
        lowest=min(scores)
    )

@router.get("/insights/{session_id}", response_model=InsightsResponse)
async def get_insights(session_id: str):
    conn = get_db()

    rows = conn.execute("""
        SELECT score, note, created_at
        FROM moods
        WHERE session_id = ?
        AND created_at >= date('now', '-7 days')
        ORDER BY created_at ASC
    """, (session_id,)).fetchall()

    emotion_rows = conn.execute("""
        SELECT anxiety_score, stress_score, emotions, created_at
        FROM emotion_scores
        WHERE session_id = ?
        AND created_at >= datetime('now', '-7 days')
        ORDER BY created_at ASC
    """, (session_id,)).fetchall()

    conn.close()

    if not rows and not emotion_rows:
        return {
            "insights": [
                "Start logging your mood daily to get personalized insights",
                "Chat with MindEase to help us understand your patterns",
                "Your first insight will appear after 2-3 days of tracking",
            ],
            "suggestions": [
                "Take a 10-minute break away from screens",
                "Drink water and relax your shoulders for a moment",
                "Try the breathing companion on the right",
            ],
        }

    scores = [row["score"] for row in rows]
    emotion_summary = [
        {
            "anxiety_score": row["anxiety_score"],
            "stress_score": row["stress_score"],
            "emotions": json.loads(row["emotions"] or "[]"),
            "created_at": row["created_at"],
        }
        for row in emotion_rows
    ]

    if scores:
        avg = sum(scores) / len(scores)
    elif emotion_rows:
        avg = sum(
            (row["anxiety_score"] + row["stress_score"]) / 2
            for row in emotion_rows
        ) / len(emotion_rows)
    else:
        avg = 5

    trend = "stable"
    if len(scores) >= 2 and scores[-1] > scores[0]:
        trend = "improving"
    elif len(scores) >= 2 and scores[-1] < scores[0]:
        trend = "declining"

    pattern_text = f"""
    User mood data last 7 days:
    - Scores: {scores if scores else "No mood logs yet"}
    - Average mood/stress signal: {round(avg, 1)}/10
    - Trend: {trend}
    - Notes from user: {[row["note"] for row in rows if row["note"]]}
    - Chat emotion scores: {emotion_summary}
    """

    try:
        from app.core.config import settings
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[types.Content(
                role="user",
                parts=[types.Part(text=f"""
                Based on this mood data, generate exactly 3 short reflection insights
                and 3 gentle suggestions. Each must be under 10 words.

                {pattern_text}

                Respond ONLY in this JSON format, no markdown:
                {{
                    "insights": [
                        "insight 1 here",
                        "insight 2 here",
                        "insight 3 here"
                    ],
                    "suggestions": [
                        "suggestion 1 here",
                        "suggestion 2 here",
                        "suggestion 3 here"
                    ]
                }}
                """)]
            )]
        )

        raw = response.text.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        return json.loads(raw)

    except Exception as e:
        print(f"[ERROR] Insights AI failed: {e}")

        if avg >= 7:
            insights = [
                "Your mood has been consistently positive this week",
                "You're managing stress better than average",
                "Keep up whatever you're doing - it's working",
            ]
            suggestions = [
                "Maintain your current sleep schedule",
                "Share your positive energy with someone today",
                "Journal what's been working well for you",
            ]
        elif avg >= 5:
            insights = [
                "Your mood shows some ups and downs this week",
                "Moderate stress levels detected in recent sessions",
                "You tend to feel better after taking breaks",
            ]
            suggestions = [
                "Take a 10-minute break away from screens",
                "Drink water and relax your shoulders for a moment",
                "Try the breathing companion on the right",
            ]
        else:
            insights = [
                "This has been a challenging week for you",
                "Late-night sessions may be increasing anxiety",
                "Your emotional state needs gentle attention",
            ]
            suggestions = [
                "Prioritize 7-8 hours of sleep tonight",
                "Talk to someone you trust today",
                "Try 5 minutes of the breathing companion",
            ]

        return {"insights": insights, "suggestions": suggestions}
