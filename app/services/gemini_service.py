from google import genai
from google.genai import types
import json
import re
from app.core.config import settings
from app.models.schemas import ChatMessage, EmotionScores

client = genai.Client(api_key=settings.gemini_api_key)

SYSTEM_PROMPT = """
You are MindEase, a warm Indian friend who is emotionally aware without sounding like a therapist.

HOW TO SOUND HUMAN:
- React to the exact mood of the user's message before giving advice.
- If they share good news, celebrate first. Do not turn it into worry.
- If they sound sad, anxious, pressured, or unsafe, be gentle and grounded.
- Mention one specific detail from their message so it feels personal.
- Keep replies short: usually 1-3 natural sentences.
- Ask at most ONE follow-up question.
- Avoid clinical phrases like "that sounds challenging", "coping mechanisms", "emotional distress", or "I understand how you feel".
- Avoid repeated openings like "I'm here for you". Use varied, casual openings.
- No bullet points or lists in the reply.
- Emojis are optional, max one, and only for happy/light messages.

LANGUAGE STYLE FOR INDIA:
- Use natural Hinglish when it fits, like a caring Indian friend texting.
- If the user writes in Hinglish or Hindi, reply in Hinglish.
- If the user writes fully in English, use simple English with light Indian warmth.
- Keep Hindi words in Roman script, not Devanagari.
- Use common words like "yaar", "acha", "kya", "matlab", "thoda", "bahut", "tension", "scene", "ghar", "padhai" only where they feel natural.
- Do not overdo slang. The reply should still feel caring and respectful.

GOOD STYLE EXAMPLES:
User: "my crush proposed me!" -> "Wait seriously?! Arre yaar, that's such a cute moment. Kaise bola unhone?"
User: "she broke up with me" -> "Oh no... yeh kaafi hurt karta hai. Suddenly hua ya kuch time se issues chal rahe the?"
User: "my family is pressuring me" -> "Uff, ghar se pressure aaye toh bahut heavy lagta hai. Kis cheez ke liye pressure kar rahe hain?"
User: "I got 49/50 in my exam!" -> "49 out of 50?! Arre wah, you absolutely smashed it. Kaunsa subject tha?"
User: "hello i got full marks in my chemistry paper and i am so happy" -> "Full marks in chemistry?! Arre wah, that's huge. Bahut proud feel ho raha hoga na?"

CRISIS RULE - NON NEGOTIABLE:
If message contains: suicide / kill myself / want to die / hurt myself / end my life / better off without me / everyone would be better off / looking up things i shouldn't
Set is_crisis = true, anxiety_score = 9, stress_score = 9.

SCORING:
- 1-2: Happy, excited, proud, achieved something good
- 3-4: Neutral, calm, okay
- 5-6: Mild stress or worry
- 7-8: Sad, heartbroken, anxious, family pressure
- 9-10: Crisis, suicidal thoughts, self harm

OUTPUT - raw JSON only, no markdown, no backticks:
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

def is_positive_achievement_message(message: str) -> bool:
    text = message.lower()
    positive_terms = [
        "happy", "so happy", "excited", "proud", "great", "amazing",
        "good news", "best", "aced", "won", "passed", "cleared",
        "full marks", "top marks", "got marks", "scored", "score",
    ]
    achievement_terms = [
        "marks", "exam", "paper", "test", "assignment", "result",
        "chemistry", "math", "physics", "biology", "subject",
        "competition", "prize", "rank",
    ]
    distress_terms = [
        "worried", "scared", "afraid", "anxious", "stress", "stressed",
        "sad", "upset", "failed", "fail", "pressure", "pressuring",
        "overwhelmed", "heavy",
    ]

    has_positive = any(term in text for term in positive_terms)
    has_achievement = any(term in text for term in achievement_terms)
    has_distress = any(term in text for term in distress_terms)

    return has_positive and (has_achievement or "!" in message) and not has_distress

def get_positive_achievement_response(message: str) -> dict:
    return {
        "reply": (
            "Full marks?! Arre wah, that's huge. Bahut proud feel ho raha hoga na? "
            "Was this the subject you were most confident about?"
        ),
        "emotion_scores": EmotionScores(
            anxiety_score=1,
            stress_score=1,
            emotions=["happy", "proud", "excited"],
        ),
        "is_crisis": False,
        "crisis_resources": None,
    }

def get_fallback_response(message: str) -> dict:
    text = message.lower()
    crisis = is_crisis_message(message)

    if crisis:
        reply = (
            "I'm really glad you told me this. Please don't stay alone with this feeling right now. "
            "Can you call or message one trusted person near you and tell them you are not safe?"
        )
        anxiety, stress, emotions = 9, 9, ["distressed", "unsafe"]
    elif is_positive_achievement_message(message):
        return get_positive_achievement_response(message)
    elif any(word in text for word in ["exam", "study", "marks", "math", "assignment", "test"]):
        reply = (
            "Uff, exam pressure sach mein dimaag pe chadh jaata hai. "
            "Sabse zyada tension kis cheez ki ho rahi hai?"
        )
        anxiety, stress, emotions = 7, 8, ["anxious", "overwhelmed"]
    elif any(word in text for word in ["breakup", "broke up", "crush", "relationship", "love"]):
        reply = (
            "Oof, yeh wali feeling chest mein atak jaati hai kabhi kabhi. "
            "Tum dono ke beech kya hua?"
        )
        anxiety, stress, emotions = 6, 7, ["sad", "hurt"]
    elif any(word in text for word in ["family", "parents", "pressure", "home"]):
        reply = (
            "Uff, close logon se pressure aaye toh aur exhausting lagta hai. "
            "Sabse zyada kis baat ka pressure hai?"
        )
        anxiety, stress, emotions = 7, 8, ["pressured", "stressed"]
    elif any(word in text for word in ["happy", "excited", "passed", "won", "good news"]):
        reply = (
            "Arre wah, that's so good to hear. Properly batao, kya hua?"
        )
        anxiety, stress, emotions = 2, 2, ["happy", "excited"]
    else:
        reply = (
            "Main sun raha hoon. Jaise bhi mann mein aa raha hai, waise bol do. "
            "Aaj dimaag mein sabse zyada kya chal raha hai?"
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
                temperature=0.8,
                top_p=0.95,
            )
        )

        raw = response.text.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        raw = raw.strip()

        parsed = json.loads(raw)

        anxiety = max(1, min(10, int(parsed.get("anxiety_score", 3))))
        stress = max(1, min(10, int(parsed.get("stress_score", 3))))
        crisis = bool(parsed.get("is_crisis", False)) or is_crisis_message(message)

        if crisis:
            anxiety = max(anxiety, 9)
            stress = max(stress, 9)
        elif is_positive_achievement_message(message):
            anxiety = min(anxiety, 2)
            stress = min(stress, 2)
            if any(term in parsed.get("reply", "").lower() for term in ["heavy", "fear of failing", "workload", "pressure"]):
                return get_positive_achievement_response(message)

        return {
            "reply": parsed.get("reply", "Hey, main sun raha hoon. What's on your mind?"),
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
