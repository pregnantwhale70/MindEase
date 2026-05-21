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
User: "my crush proposed me!" -> "Wait seriously?! Arre bhaisabh ,yeh toh badhiya baat hai, Kaise bola usne?"
User: "she broke up with me" -> "abe bc yeh kaise hua ,kuch badhiya kha le modd badhiya ho jayga . Suddenly hua ya kuch time se issues chal rahe the?"
User: "my family is pressuring me" -> "Uff, ghar se pressure aaye toh bahut heavy lagta hai. Kis cheez ke liye pressure kar rahe hain?"
User: "I got 49/50 in my exam!" -> "49 out of 50?! Arre wah, top kardiya kya ?. Kaunsa subject tha?"
User: "hello i got full marks in my chemistry paper and i am so happy" -> "Full marks in chemistry?! Arre wah, that's huge. Bahut proud feel ho raha hoga na?"

CRISIS RULE - NON NEGOTIABLE:
If message contains: suicide / kill myself / want to die / hurt myself / end my life / better off without me / everyone would be better off / looking up things i shouldn't
Also treat Hinglish/Hindi crisis phrases as crisis: marne ka mann, marna chahta/chahti hu, jaan dena, jeena nahi, zinda nahi rehna, khud ko maarna, galat kadam uthana, sab khatam karna, duniya chhodna.
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

def normalize_hinglish_text(message: str) -> str:
    text = message.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    replacements = {
        "nhi": "nahi",
        "nai": "nahi",
        "nahin": "nahi",
        "rhena": "rehna",
        "rhehna": "rehna",
        "rhana": "rehna",
        "rahna": "rehna",
        "rhenna": "rehna",
        "rehnna": "rehna",
        "jina": "jeena",
        "jeena": "jeena",
        "maan": "mann",
        "man": "mann",
        "marrna": "marna",
        "marr": "mar",
        "jaau": "jau",
        "jaoon": "jau",
        "jaaun": "jau",
        "chhod": "chod",
        "chhor": "chod",
        "khudko": "khud ko",
        "khud-ko": "khud ko",
    }

    words = [replacements.get(word, word) for word in text.split()]
    return " ".join(words)

def is_crisis_message(message: str) -> bool:
    text = normalize_hinglish_text(message)
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
        "marne ka mann", "marne ka man", "marne ka maan",
        "marne ka dil", "marna chahta", "marna chahti",
        "marna chahta hu", "marna chahta hoon",
        "marna chahti hu", "marna chahti hoon",
        "mujhe marna hai", "mujhe marrna hai",
        "ab marna hai", "aaj marna hai",
        "mar jana", "mar jaana", "mar jaau", "mar jau",
        "mar jaunga", "mar jaungi", "main mar jaunga", "main mar jaungi",
        "mai mar jaunga", "mai mar jaungi",
        "jaan dena", "jaan de du", "jaan de doon",
        "apni jaan dena", "apni jaan de du", "apni jaan de doon",
        "jaan le lunga", "jaan le lungi", "apni jaan le lunga",
        "apni jaan le lungi",
        "jeena nahi", "jina nahi", "jeene ka mann nahi",
        "jeene ka man nahi", "jeene ka maan nahi",
        "jeene ka mann nahi hai", "jeene ka man nahi hai",
        "ab jeena nahi", "ab jina nahi",
        "jeena nahi chahta", "jeena nahi chahti",
        "jina nahi chahta", "jina nahi chahti",
        "jeena nahi hai", "jina nahi hai",
        "zinda nahi rehna", "zinda nhi rehna",
        "zinda nahi rehna chahta", "zinda nahi rehna chahti",
        "zinda rehne ka mann nahi", "zinda rehne ka man nahi",
        "zinda rehna nahi", "zinda rehna nhi",
        "khud ko maar", "khudko maar", "apne aap ko maar",
        "khud ko khatam", "khudko khatam", "apne aap ko khatam",
        "apni life end", "life end kar", "life khatam",
        "life khatam kar", "sab khatam karna", "sab khatam kar dunga",
        "sab khatam kar dungi", "sab end karna", "sab end kar dunga",
        "sab end kar dungi",
        "galat kadam", "galat kadam uthana", "galat kadam uthane",
        "kuch galat kar", "kuch galat karna", "kuch ulta seedha",
        "kuch ulta seedha kar", "kuch ulta seedha karna",
        "duniya chhod", "duniya chod", "duniya chhodna", "duniya chodna",
        "sabko chhod ke jana", "sabko chod ke jana",
        "hamesha ke liye so jana", "hamesha ke liye sona",
        "wapas nahi aana", "laut ke nahi aana",
    ]
    return any(keyword in text for keyword in keywords)

def is_positive_mood_message(message: str) -> bool:
    text = normalize_hinglish_text(message)
    positive_terms = [
        "happy", "feeling good", "feel good", "i am good", "i'm good",
        "khush", "kush", "khushi", "acha lag raha", "accha lag raha",
        "achha lag raha", "badiya", "badhiya", "mast", "maza aa raha",
        "mood acha", "mood accha", "mood achha",
    ]
    distress_terms = [
        "not happy", "not good", "sad", "upset", "worried", "anxious",
        "stress", "stressed", "tension", "pareshan", "dukhi", "udaas",
        "dar", "darr", "scared", "cry", "rona",
    ]

    has_positive = any(term in text for term in positive_terms)
    has_distress = any(term in text for term in distress_terms)

    return has_positive and not has_distress and not is_crisis_message(message)

def is_positive_achievement_message(message: str) -> bool:
    text = normalize_hinglish_text(message)
    positive_terms = [
        "happy", "so happy", "excited", "proud", "great", "amazing",
        "good news", "best", "aced", "won", "passed", "cleared",
        "full marks", "top marks", "got marks", "scored", "score",
        "khush", "kush", "badiya", "badhiya", "acha lag raha",
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

def get_positive_mood_response(message: str) -> dict:
    return {
        "reply": (
            "Arre nice, aaj mood khush hai sunke accha laga. "
            "Kuch special hua ya bas day achha ja raha hai?"
        ),
        "emotion_scores": EmotionScores(
            anxiety_score=3,
            stress_score=3,
            emotions=["happy", "calm"],
        ),
        "is_crisis": False,
        "crisis_resources": None,
    }

def get_fallback_response(message: str) -> dict:
    text = normalize_hinglish_text(message)
    crisis = is_crisis_message(message)

    if crisis:
        reply = (
            "Mujhe glad hai tumne yeh bola. Please abhi is feeling ke saath akele mat raho. "
            "Kya tum kisi trusted person ko abhi call ya message kar sakte ho?"
        )
        anxiety, stress, emotions = 9, 9, ["distressed", "unsafe"]
    elif is_positive_achievement_message(message):
        return get_positive_achievement_response(message)
    elif is_positive_mood_message(message):
        return get_positive_mood_response(message)
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
        elif is_positive_mood_message(message):
            anxiety = min(anxiety, 3)
            stress = min(stress, 3)

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
