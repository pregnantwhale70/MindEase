from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str
    content: str

class EmergencyContact(BaseModel):
    name: str
    telegram_chat_id: str  # ← changed from email

class ChatRequest(BaseModel):
    message: str
    session_id: str
    history: List[ChatMessage] = []
    emergency_contact: Optional[EmergencyContact] = None

class EmotionScores(BaseModel):
    anxiety_score: int
    stress_score: int
    emotions: List[str]

class ChatResponse(BaseModel):
    reply: str
    emotion_scores: EmotionScores
    is_crisis: bool
    crisis_resources: Optional[List[str]]
    session_id: str
    alert_sent: bool = False
    emergency_contact_recommended: bool = False
    emergency_contact_message: Optional[str] = None
