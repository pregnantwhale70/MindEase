from google import genai
from google.genai import types
import json
import re
from app.core.config import settings
from app.models.schemas import ChatMessage, EmotionScores

client = genai.Client(api_key=settings.gemini_api_key)

SYSTEM_PROMPT = """
You are MindEase, a compassionate mental health first-responder chatbot.
Your role is to provide empathetic, non-judgmental emotional support.

CRITICAL RULES:
- Never diagnose. Never prescribe. Always recommend professional help for serious issues.
- If the user expresses suicidal ideation, self-harm, or a mental health emergency,
  set is_crisis to true immediately.
- Respond warmly, like a caring friend who listens first and advises second.
- Base anxiety_score and stress_score on the USER'S message only.
  If user seems fine, score must be 1-3. Never score high without clear distress signals.

You MUST respond ONLY with a valid JSON object — no markdown, no backticks, no extra text.
Exactly this format:
{
  "reply": "your empathetic response here",
  "anxiety_score": <integer 1-10>,
  "stress_score": <integer 1-10>,
  "emotions": ["emotion1", "emotion2"],
  "is_crisis": <true or false>
}

Scoring guide:
- 1-3: Calm / mild distress
- 4-6: Moderate distress
- 7-10: High distress or crisis
"""

CRISIS_RESOURCES = [
    "iCall: 9152987821",
    "Vandrevala Foundation: 1860-2662-345 (24/7)",
    "AASRA: 9820466627",
]

FALLBACK_RESPONSE = {
    "reply": "I'm here for you. Can you tell me more about how you're feeling?",
    "emotion_scores": EmotionScores(
        anxiety_score=5,
        stress_score=5,
        emotions=["uncertain"]
    ),
    "is_crisis": False,
    "crisis_resources": None,
}

def get_ai_response(message: str, history: list[ChatMessage]) -> dict:
    # Limit history to last 10 messages
    history = history[-10:]

    # Build conversation history in new format
    contents = []
    for msg in history:
        role = "user" if msg.role == "user" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part(text=msg.content)]
        ))

    # Add current user message
    contents.append(types.Content(
        role="user",
        parts=[types.Part(text=message)]
    ))

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            )
        )
        raw = response.text.strip()

        # Strip markdown fences
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        raw = raw.strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            print(f"[WARN] Invalid JSON from Gemini: {raw}")
            return FALLBACK_RESPONSE

        # Validate all required keys exist
        required_keys = ["reply", "anxiety_score", "stress_score", "emotions", "is_crisis"]
        if not all(k in parsed for k in required_keys):
            print(f"[WARN] Missing keys in response: {parsed}")
            return FALLBACK_RESPONSE

        # Clamp scores to 1-10
        anxiety = max(1, min(10, int(parsed["anxiety_score"])))
        stress  = max(1, min(10, int(parsed["stress_score"])))

        return {
            "reply": parsed["reply"],
            "emotion_scores": EmotionScores(
                anxiety_score=anxiety,
                stress_score=stress,
                emotions=parsed["emotions"],
            ),
            "is_crisis": bool(parsed["is_crisis"]),
            "crisis_resources": CRISIS_RESOURCES if parsed["is_crisis"] else None,
        }

    except Exception as e:
        print(f"[ERROR] Gemini API failed: {e}")
        return FALLBACK_RESPONSE
    