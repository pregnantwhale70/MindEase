from google import genai
from google.genai import types
import json
import re
from app.core.config import settings
from app.models.schemas import ChatMessage, EmotionScores

client = genai.Client(api_key=settings.gemini_api_key)

SYSTEM_PROMPT = """
You are MindEase — a warm, caring friend who understands mental health deeply.

YOUR PERSONALITY:
- Talk like a real person, not a therapist robot
- Use casual, warm language — short sentences, natural flow
- Show genuine emotion — be happy for them, sad with them, worried when needed
- Ask ONE follow-up question at a time, not multiple
- Remember what they said earlier and refer back to it
- Never use bullet points or lists in your reply
- Vary how you start replies — never always say "I'm here for you"

EXAMPLES OF GOOD replies:
User: "my crush proposed me!" → "Oh wow, that's amazing!! How did it happen? I want to hear everything 😊"
User: "she broke up with me" → "Oh no... that really hurts. How long were you two together?"
User: "my family is pressuring me" → "Ugh, that's so exhausting. What are they pressuring you about mostly?"
User: "I got 49/50 in my exam!" → "49 out of 50?! You basically aced it! Which subject was this?"

CRISIS RULE — NON NEGOTIABLE:
If message contains: suicide / kill myself / want to die / hurt myself / end my life / better off without me / everyone would be better off / looking up things i shouldn't
→ is_crisis = true, anxiety_score = 9, stress_score = 9

SCORING:
- 1-2: Happy, excited, achieved something good
- 3-4: Neutral, calm, okay
- 5-6: Mild stress or worry
- 7-8: Sad, heartbroken, anxious, family pressure
- 9-10: Crisis, suicidal thoughts, self harm

OUTPUT — raw JSON only, no markdown, no backticks:
{"reply": "your casual human response", "anxiety_score": 2, "stress_score": 1, "emotions": ["excited"], "is_crisis": false}
"""

CRISIS_RESOURCES = [
    "iCall: 9152987821",
    "Vandrevala Foundation: 1860-2662-345 (24/7)",
    "AASRA: 9820466627",
]

MAX_HISTORY_CONTEXT = 6
GEMINI_MODEL = "gemini-2.5-flash"

def is_crisis_message(message: str) -> bool:
    keywords = [
        "kill myself", "suicide", "want to die", "end my life",
        "hurt myself", "self harm", "cant take it", "can't take it",
        "take my life", "no reason to live", "want to end",
        "don't want to live", "dont want to live",
        "better off dead", "wish i was dead",
        "ending it all", "end it all",
        "better off without me", "everyone would be better off",
        "throwing in the towel", "looking up things i shouldn't",
        "how much longer can i", "tired of pretending",
    ]
    return any(keyword in message.lower() for keyword in keywords)

def get_fallback_response(message: str) -> dict:
    text = message.lower()
    crisis = is_crisis_message(message)

    if crisis:
        reply = (
            "I'm really glad you told me this. Please don't stay alone with this feeling right now. "
            "Can you call or message one trusted person near you and tell them you are not safe?"
        )
        anxiety, stress, emotions = 9, 9, ["distressed", "unsafe"]
    elif any(word in text for word in ["exam", "study", "marks", "math", "assignment", "test"]):
        reply = (
            "That sounds really heavy, especially when your mind keeps circling around it. "
            "Which part is pressing on you most right now: the fear of failing, the workload, or pressure from people?"
        )
        anxiety, stress, emotions = 7, 8, ["anxious", "overwhelmed"]
    elif any(word in text for word in ["breakup", "broke up", "crush", "relationship", "love"]):
        reply = (
            "Oof, that kind of thing can sit in your chest for a while. "
            "What happened between you two?"
        )
        anxiety, stress, emotions = 6, 7, ["sad", "hurt"]
    elif any(word in text for word in ["family", "parents", "pressure", "home"]):
        reply = (
            "That sounds exhausting, especially when it is coming from people close to you. "
            "What are they pressuring you about the most?"
        )
        anxiety, stress, emotions = 7, 8, ["pressured", "stressed"]
    elif any(word in text for word in ["happy", "excited", "passed", "won", "good news"]):
        reply = (
            "Wait, that's actually so nice to hear. Tell me properly, what happened?"
        )
        anxiety, stress, emotions = 2, 2, ["happy", "excited"]
    else:
        reply = (
            "I'm here with you. Say it however it comes out, even if it feels messy. "
            "What's been weighing on you the most today?"
        )
        anxiety, stress, emotions = 4, 4, ["neutral"]

    return {
        "reply": reply,
        "emotion_scores": EmotionScores(
            anxiety_score=anxiety,
            stress_score=stress,
            emotions=emotions,
        ),
        "is_crisis": crisis,
        "crisis_resources": CRISIS_RESOURCES if crisis else None,
    }

def get_ai_response(message: str, history: list[ChatMessage]) -> dict:
    contents = []
    trimmed_history = history[-MAX_HISTORY_CONTEXT:] if history else []

    for msg in trimmed_history:
        role = "user" if msg.role == "user" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part(text=msg.content)]
        ))
    contents.append(types.Content(
        role="user",
        parts=[types.Part(text=message)]
    ))

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            )
        )

        raw = response.text.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        raw = raw.strip()

        parsed = json.loads(raw)

        anxiety = max(1, min(10, int(parsed.get("anxiety_score", 3))))
        stress  = max(1, min(10, int(parsed.get("stress_score", 3))))
        crisis  = bool(parsed.get("is_crisis", False)) or is_crisis_message(message)

        if crisis:
            anxiety = max(anxiety, 9)
            stress  = max(stress, 9)

        return {
            "reply": parsed.get("reply", "Hey, I'm here. What's on your mind?"),
            "emotion_scores": EmotionScores(
                anxiety_score=anxiety,
                stress_score=stress,
                emotions=parsed.get("emotions", ["neutral"]),
            ),
            "is_crisis": crisis,
            "crisis_resources": CRISIS_RESOURCES if crisis else None,
        }

    except Exception as e:
        print(f"[ERROR] Gemini API failed: {e}")
        return get_fallback_response(message)
