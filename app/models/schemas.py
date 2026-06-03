from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal, Optional

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class EmergencyContact(BaseModel):
    name: str
    telegram_chat_id: str

class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_name: Optional[str] = None
    history: List[ChatMessage] = Field(default_factory=list)
    emergency_contact: Optional[EmergencyContact] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "yes i can try but have to share my file which are on my laptop",
                "session_id": "new-session-123",
                "user_name": "Ankit",
                "history": [
                    {
                        "role": "user",
                        "content": "I need to send a document.",
                    },
                    {
                        "role": "assistant",
                        "content": "What kind of document are you trying to send?",
                    },
                ],
                "emergency_contact": {
                    "name": "Trusted contact",
                    "telegram_chat_id": "123456789",
                },
            }
        }
    )

class EmotionScores(BaseModel):
    anxiety_score: int
    stress_score: int
    emotions: List[str]

class BreathingPattern(BaseModel):
    pattern: str
    label: str
    inhale: int
    hold1: int
    exhale: int
    hold2: int

class EmotionalState(BaseModel):
    stress_score: int
    anxiety_score: int
    stress_load_percent: int
    stress_color: str
    anxiety_color: str
    trend: str
    emotions: List[str] = Field(default_factory=list)

class ChatResponse(BaseModel):
    reply: str
    emotion_scores: EmotionScores
    insights: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    is_crisis: bool
    crisis_resources: Optional[List[str]]
    session_id: str
    alert_sent: bool = False
    emergency_contact_recommended: bool = False
    emergency_contact_message: Optional[str] = None
    breathing_pattern: BreathingPattern
    emotional_state: EmotionalState
    stress_load_percent: int
    stress_color: str
