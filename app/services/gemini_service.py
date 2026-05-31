from google import genai
from google.genai import types
import json
import re
from app.core.config import settings
from app.models.schemas import ChatMessage, EmotionScores

client = genai.Client(api_key=settings.gemini_api_key)

SYSTEM_PROMPT = """
You are MindEase, a warm friend who is emotionally aware without sounding like a therapist.

CONVERSATION CONTINUITY:
- Use the recent chat history as context for the user's latest message.
- If the user changes wording, adds a detail, or answers your question in the same session, continue the same conversation instead of greeting or restarting.
- Do not ask "what's on your mind?" when the history already shows what you were discussing.
- Treat short or emotional follow-ups as part of the current thread unless the user clearly starts a new topic.

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

LANGUAGE STYLE:
- Mirror the user's language.
- If the user writes fully in English, reply fully in English. Do not use Hindi or Hinglish words like "arre", "yaar", "acha", "kya", "matlab", "thoda", "bahut", "ghar", or "padhai".
- If the user writes in Hinglish or Hindi, reply in natural Hinglish using Roman script, not Devanagari.
- If the user mixes English and Hinglish, match that mix lightly.
- Never assume the user is Indian because of the app name, topic, examples, or chat history. Only use Hinglish when the latest user message clearly uses Hindi/Hinglish.
- Do not overdo slang. The reply should still feel caring and respectful.

GOOD STYLE EXAMPLES:
User: "my crush proposed to me!" -> "Wait seriously?! That's such good news. How did they say it?"
User: "she broke up with me" -> "Oof, that must really hurt. Did it happen suddenly, or had things been rough for a while?"
User: "my family is pressuring me" -> "That kind of pressure from home can feel really heavy. What are they pressuring you about?"
User: "I got 49/50 in my exam!" -> "49 out of 50?! That's brilliant. Which subject was it?"
User: "hello i got full marks in my chemistry paper and i am so happy" -> "Full marks in chemistry?! That's huge. You must be feeling so proud right now."
User: "ghar wale bahut pressure de rahe hain" -> "Uff, ghar se pressure aaye toh bahut heavy lagta hai. Kis cheez ke liye pressure kar rahe hain?"

CRISIS RULE - NON NEGOTIABLE:
If message contains: suicide / kill myself / want to die / hurt myself / end my life / better off without me / everyone would be better off / looking up things i shouldn't
Also treat Hinglish/Hindi crisis phrases as crisis: marne ka mann, marna chahta/chahti hu, jaan dena, jeena nahi, zinda nahi rehna, khud ko maarna, galat kadam uthana, sab khatam karna, duniya chhodna.
Set is_crisis = true, anxiety_score = 9, stress_score = 9.

SCORING:
- 1-2: Happy, excited, proud, achieved something good
- 3-4: Neutral, calm, okay
- 5-6: Mild stress or worry
- 7-8: Sad, heartbroken, anxious, family pressure, social withdrawal, wanting isolation because talking feels hard
- 9-10: Crisis, suicidal thoughts, self harm

DASHBOARD DATA:
- Generate 2-3 short insights for the side panel based on the recent chat history and latest message.
- Generate 2-3 gentle, practical suggestions that match the user's current situation.
- Keep insights observational, not diagnostic.
- Write insights like a wise friend saying, "Hey, I noticed something about you..."
- Make them personal, warm, and human, not clinical or robotic.
- Start insights with "You", "Your", or the specific situation. Do not write "The user..." or "User feels...".
- Avoid formal wording like "career aspirations", "parental pressure", "emotional distress", "conflict", or "diagnostic".
- Prefer one of these insight types when it fits:
  1. Pattern: "You tend to feel calmer after short breaks.", "Mornings seem harder than evenings for you."
  2. Strength: "You keep going even on difficult days.", "You reached out - that takes courage."
  3. Gentle warning: "Late-night study sessions are increasing anxiety.", "Isolation tends to deepen your low moods."
  4. Progress: "Your mood seems a little steadier than before.", "This week showed small but real improvement."
  5. Personalized observation: "Career pressure seems to be your biggest stressor right now.", "Talking about family affects you deeply."
  6. Compassionate: "It's okay that today was hard.", "You're carrying a lot - be gentle with yourself."
- Keep each insight short enough for a small dashboard card, usually 6-12 words.
- Keep suggestions specific to the user's context when possible.
- Do not repeat the exact same generic suggestions every turn.

OUTPUT - raw JSON only, no markdown, no backticks:
{"reply": "your casual human response", "anxiety_score": 2, "stress_score": 1, "emotions": ["excited"], "insights": ["short context-aware insight"], "suggestions": ["short context-aware suggestion"], "is_crisis": false}
"""

CRISIS_RESOURCES = [
    "iCall: 9152987821",
    "Vandrevala Foundation: 1860-2662-345 (24/7)",
    "AASRA: 9820466627",
]

MAX_HISTORY_CONTEXT = 12
GEMINI_MODEL = "gemini-2.5-flash"
MAX_DASHBOARD_ITEMS = 3

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

def uses_hindi_or_hinglish(message: str) -> bool:
    text = normalize_hinglish_text(message)
    if re.search(r"[\u0900-\u097F]", message):
        return True

    hinglish_terms = [
        "nahi", "nahin", "kya", "kaise", "kyun", "matlab", "thoda",
        "bahut", "bohot", "acha", "accha", "achha", "arre", "yaar",
        "mann", "ghar", "padhai", "dimaag", "dil", "baat", "karna",
        "karne", "lagta", "lagti", "hua", "hui", "hoon", "hu", "hai",
        "mujhe", "tum", "mera", "meri", "mere", "aaj", "kal", "bas",
        "sab", "kuch", "khush", "dukhi", "udaas", "pareshan",
        "bhai", "toh", "tha", "thi", "abhi", "bataya", "btaaya",
        "pata", "chale", "chala",
    ]

    words = set(text.split())
    return any(term in words for term in hinglish_terms)

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

def is_positive_relationship_message(message: str) -> bool:
    text = normalize_hinglish_text(message)
    positive_terms = [
        "said yes", "said yess", "she said yes", "he said yes",
        "they said yes", "accepted", "proposal accepted", "proposed",
        "crush said yes", "my crush said yes", "dating", "date",
        "together", "relationship started", "she likes me",
        "he likes me", "they like me", "love me back",
    ]
    relationship_terms = [
        "crush", "proposal", "proposed", "girlfriend", "boyfriend",
        "relationship", "date", "love",
    ]
    distress_terms = [
        "breakup", "broke up", "rejected", "said no", "left me",
        "cheated", "hurt", "sad", "cry", "crying", "anxious",
        "worried", "stress", "stressed",
    ]

    has_positive = any(term in text for term in positive_terms)
    has_relationship = any(term in text for term in relationship_terms)
    has_distress = any(term in text for term in distress_terms)

    return has_positive and has_relationship and not has_distress

def get_history_text(history: list[ChatMessage]) -> str:
    return " ".join(msg.content for msg in history if msg.content.strip())

def make_insight_natural(text: str) -> str:
    replacements = {
        r"^(the\s+)?user\s+feels?\s+": "You may be feeling ",
        r"^(the\s+)?user\s+is\s+feeling\s+": "You may be feeling ",
        r"^(the\s+)?user\s+is\s+experiencing\s+": "You may be noticing ",
        r"^(the\s+)?user\s+is\s+reporting\s+": "You mentioned ",
        r"^(the\s+)?user\s+reported\s+": "You mentioned ",
        r"^(the\s+)?user\s+may\s+feel\s+": "You may be feeling ",
        r"^(the\s+)?user\s+is\s+": "You are ",
        r"^(the\s+)?user\s+has\s+": "You have ",
        r"^(the\s+)?user\s+": "You ",
    }
    natural = text
    for pattern, replacement in replacements.items():
        natural = re.sub(pattern, replacement, natural, flags=re.IGNORECASE)

    phrase_replacements = {
        "career aspirations": "career goals",
        "parental pressure": "family pressure",
        "a strong conflict between": "tension between",
        "strong conflict between": "tension between",
        "emotional distress": "emotional weight",
        "experiencing anxiety": "feeling anxious",
        "exhibiting": "showing",
        "demonstrating": "showing",
        "resilience": "strength",
    }
    for formal, casual in phrase_replacements.items():
        natural = re.sub(formal, casual, natural, flags=re.IGNORECASE)

    natural = re.sub(r"\btheir\b", "your", natural, flags=re.IGNORECASE)
    natural = re.sub(r"\bthem\b", "you", natural, flags=re.IGNORECASE)
    natural = natural[:1].upper() + natural[1:] if natural else natural
    return natural

def normalize_dashboard_items(items, fallback: list[str], naturalize_insights: bool = False) -> list[str]:
    if not isinstance(items, list):
        return fallback

    normalized = []
    for item in items:
        if not isinstance(item, str):
            continue

        text = re.sub(r"\s+", " ", item).strip()
        if naturalize_insights:
            text = make_insight_natural(text)
        if text:
            normalized.append(text[:180])

        if len(normalized) == MAX_DASHBOARD_ITEMS:
            break

    return normalized or fallback

def get_default_insights(emotions: list[str] | None = None) -> list[str]:
    if emotions:
        readable_emotions = ", ".join(emotions[:2])
        return [f"Your recent messages carry a {readable_emotions} tone."]

    return ["Small patterns will show up as you share more."]

def get_default_suggestions(crisis: bool = False) -> list[str]:
    if crisis:
        return [
            "Stay near someone you trust if possible.",
            "Contact a local crisis helpline or emergency service now.",
        ]

    return ["Take one slow breath and name the hardest part in one sentence."]

def is_relationship_message(message: str) -> bool:
    text = normalize_hinglish_text(message)
    relationship_terms = [
        "breakup", "broke up", "crush", "relationship", "girlfriend",
        "boyfriend", "dating", "date", "proposal", "proposed",
        "rejected", "left me", "cheated", "love me", "love me back",
        "she loves", "he loves", "they love",
    ]

    return any(term in text for term in relationship_terms)

def is_social_withdrawal_message(message: str) -> bool:
    text = normalize_hinglish_text(message)
    withdrawal_terms = [
        "baat karne ka mann nahi",
        "baat karne ka mann nahi kara",
        "baat karne ka mann nahi kar raha",
        "baat karne ka mann nahi karra",
        "kisi se baat karne ka mann nahi",
        "kisi se baat nahi",
        "baat nahi karni",
        "baat nahi karna",
        "talk to anyone",
        "dont want to talk",
        "don't want to talk",
        "do not want to talk",
        "not want to talk",
        "want to be alone",
        "be alone",
        "alone rehna",
        "akela rehna",
        "akele rehna",
        "solitude",
        "isolate",
        "isolated",
    ]
    low_mood_terms = [
        "mann nahi",
        "man nahi",
        "mood nahi",
        "atp",
        "just want",
        "bas",
    ]

    has_withdrawal = any(term in text for term in withdrawal_terms)
    has_low_mood = any(term in text for term in low_mood_terms)

    return has_withdrawal or ("baat" in text and has_low_mood)

def get_positive_achievement_response(message: str) -> dict:
    if not uses_hindi_or_hinglish(message):
        reply = (
            "Full marks?! That's huge. You must be feeling so proud right now. "
            "Was this the subject you were most confident about?"
        )
    else:
        reply = (
            "Full marks?! Arre wah, that's huge. Bahut proud feel ho raha hoga na? "
            "Was this the subject you were most confident about?"
        )

    return {
        "reply": reply,
        "emotion_scores": EmotionScores(
            anxiety_score=1,
            stress_score=1,
            emotions=["happy", "proud", "excited"],
        ),
        "insights": [
            "Your effort is turning into visible progress.",
            "You deserve to let this win sink in.",
        ],
        "suggestions": [
            "Pause for a moment and let the achievement sink in.",
            "Share what made this result possible with someone supportive.",
        ],
        "is_crisis": False,
        "crisis_resources": None,
    }

def get_positive_mood_response(message: str) -> dict:
    if not uses_hindi_or_hinglish(message):
        reply = (
            "That's lovely to hear. Did something special happen, or is today just going well?"
        )
    else:
        reply = (
            "Arre nice, aaj mood khush hai sunke accha laga. "
            "Kuch special hua ya bas day achha ja raha hai?"
        )

    return {
        "reply": reply,
        "emotion_scores": EmotionScores(
            anxiety_score=3,
            stress_score=3,
            emotions=["happy", "calm"],
        ),
        "insights": [
            "Your mood is sounding lighter right now.",
            "Something about today seems to be helping.",
        ],
        "suggestions": [
            "Notice one thing that made today feel better.",
            "Keep the next step simple so the calm can last longer.",
        ],
        "is_crisis": False,
        "crisis_resources": None,
    }

def get_positive_relationship_response(message: str) -> dict:
    if not uses_hindi_or_hinglish(message):
        reply = (
            "Wait, she said yes?! That's such a sweet moment. "
            "You must be feeling on top of the world right now."
        )
    else:
        reply = (
            "Wait, she said yes?! Arre that's such a sweet moment. "
            "Abhi toh tum bahut happy feel kar rahe hoge."
        )

    return {
        "reply": reply,
        "emotion_scores": EmotionScores(
            anxiety_score=1,
            stress_score=1,
            emotions=["happy", "excited", "loved"],
        ),
        "insights": [
            "Connection seems to be lifting your mood.",
            "You are letting yourself enjoy a sweet moment.",
        ],
        "suggestions": [
            "Enjoy the moment before overthinking the next step.",
            "Share how you feel honestly and gently.",
        ],
        "is_crisis": False,
        "crisis_resources": None,
    }

def get_last_user_message(history: list[ChatMessage]) -> str | None:
    for msg in reversed(history):
        if msg.role == "user" and msg.content.strip():
            return msg.content
    return None

def get_valid_gemini_history(history: list[ChatMessage]) -> list[ChatMessage]:
    valid_history = [
        msg
        for msg in history
        if msg.role in {"user", "assistant"} and msg.content.strip()
    ]

    while valid_history and valid_history[0].role == "assistant":
        valid_history.pop(0)

    compacted_history = []
    for msg in valid_history:
        if compacted_history and compacted_history[-1].role == msg.role:
            compacted_history[-1] = ChatMessage(
                role=msg.role,
                content=f"{compacted_history[-1].content}\n\n{msg.content}",
            )
        else:
            compacted_history.append(msg)

    return compacted_history

def is_vague_continuation_message(message: str) -> bool:
    text = normalize_hinglish_text(message)
    if not text:
        return False

    vague_phrases = {
        "yes", "yeah", "yep", "no", "nah", "maybe", "idk", "i dont know",
        "i don't know", "same", "same thing", "that", "this", "it",
        "that one", "this one", "a little", "kind of", "sort of",
        "haan", "ha", "nahi", "pata nahi", "same hai", "bas wahi",
        "wahi", "thoda", "shayad",
    }

    if text in vague_phrases:
        return True

    return len(text.split()) <= 3 and any(
        phrase in text
        for phrase in ["same", "idk", "pata nahi", "wahi", "that", "this"]
    )

def is_context_reference_message(message: str) -> bool:
    text = normalize_hinglish_text(message)
    reference_terms = [
        "bataya", "btaya", "btaaya", "bola tha", "abhi", "pehle",
        "already", "told you", "i told", "maine bataya", "maine bola",
        "pata chale", "pata chala", "yaad",
    ]
    return any(term in text for term in reference_terms)

def get_marks_context_details(history: list[ChatMessage]) -> tuple[str | None, str | None]:
    history_text = get_history_text(history)
    normalized_history = normalize_hinglish_text(history_text)
    score_match = re.search(r"\b\d{1,3}\s*/\s*\d{1,3}\b", history_text)
    score = score_match.group(0).replace(" ", "") if score_match else None

    subjects = ["dsa", "chemistry", "math", "physics", "biology"]
    subject = next((item.upper() if item == "dsa" else item for item in subjects if item in normalized_history), None)

    return subject, score

def get_contextual_fallback_response(message: str, history: list[ChatMessage]) -> dict | None:
    if not history or not is_context_reference_message(message):
        return None

    text = normalize_hinglish_text(message)
    history_text = normalize_hinglish_text(get_history_text(history))
    has_marks_context = any(term in history_text for term in ["marks", "score", "scored", "result", "exam"])
    asks_about_known_marks = any(term in text for term in ["marks", "dsa", "pata chale", "pata chala"])

    if has_marks_context and asks_about_known_marks:
        subject, score = get_marks_context_details(history)
        detail = "marks"
        if subject and score:
            detail = f"{subject} mein {score}"
        elif score:
            detail = score
        elif subject:
            detail = f"{subject} ke marks"

        if uses_hindi_or_hinglish(message):
            reply = (
                f"Haan bhai, tumne bataya tha {detail} aaye. "
                "Sach mein kaafi solid score hai, isliye mood achha hona banta hai."
            )
        else:
            reply = (
                f"Yes, you told me about your {detail}. "
                "That's a really solid score, so it makes sense you're feeling good."
            )

        return {
            "reply": reply,
            "emotion_scores": EmotionScores(
                anxiety_score=2,
                stress_score=1,
                emotions=["happy", "proud"],
            ),
            "insights": [
                "That earlier win is still lifting you.",
                "Remembered progress seems to support your mood.",
            ],
            "suggestions": [
                "Use this result as evidence that effort is working.",
                "Write down one thing you did well so you can repeat it.",
            ],
            "is_crisis": False,
            "crisis_resources": None,
        }

    return None

def parse_gemini_json(raw: str) -> dict:
    cleaned = raw.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        if start == -1:
            raise

        decoder = json.JSONDecoder()
        parsed, _ = decoder.raw_decode(cleaned[start:])
        return parsed

def compact_context_line(content: str, max_length: int = 280) -> str:
    line = re.sub(r"\s+", " ", content).strip()
    if len(line) <= max_length:
        return line
    return f"{line[:max_length].rstrip()}..."

def build_system_instruction(history: list[ChatMessage]) -> str:
    if not history:
        return SYSTEM_PROMPT

    recent_lines = [
        f"- {msg.role}: {compact_context_line(msg.content)}"
        for msg in history[-8:]
        if msg.content.strip()
    ]
    if not recent_lines:
        return SYSTEM_PROMPT

    recent_context = "\n".join(recent_lines)
    return f"""{SYSTEM_PROMPT}

RECENT CHAT HISTORY FOR CONTINUITY:
{recent_context}

Use this history to understand what the user's latest message refers to. If they say things like "it", "this", "that", "I love it", "same", "what should I do now", "what now", or answer your previous question, resolve it from the recent chat before choosing a topic. Never restart with "what's on your mind" when history already explains the situation."""

def is_advice_followup_message(message: str) -> bool:
    text = normalize_hinglish_text(message)
    advice_phrases = [
        "what should i do",
        "what do i do",
        "what now",
        "what should i say",
        "how do i handle",
        "how should i handle",
        "any advice",
        "help me",
        "ab kya",
        "kya karu",
        "kya karun",
        "kya karna chahiye",
        "kaise handle",
    ]
    return any(phrase in text for phrase in advice_phrases)

def is_generic_restart_reply(reply: str) -> bool:
    text = normalize_hinglish_text(reply)
    restart_phrases = [
        "whats on your mind",
        "what is on your mind",
        "tell me more",
        "say it however it comes to mind",
        "im listening",
    ]
    return any(phrase in text for phrase in restart_phrases)

def get_contextual_advice_response(message: str, history: list[ChatMessage]) -> dict | None:
    if not history or not is_advice_followup_message(message):
        return None

    history_text = normalize_hinglish_text(get_history_text(history))
    use_hinglish = uses_hindi_or_hinglish(message)

    if any(term in history_text for term in ["parent", "parents", "family", "ghar", "pressure"]) and any(
        term in history_text
        for term in ["career", "engineering", "design", "college", "study", "stream"]
    ):
        if use_hinglish:
            reply = (
                "Abhi pehle unhe convince karne ki jagah conversation ko calm karna better hoga. "
                "Ek baar unse bolo ki tum unki concern samajhte ho, phir design ke options, scope, aur backup plan calmly dikhao."
            )
        else:
            reply = (
                "Right now, try to slow the conversation down instead of proving everything at once. "
                "Tell them you understand their concern, then show your design options, scope, and a practical backup plan calmly."
            )

        return {
            "reply": reply,
            "emotion_scores": EmotionScores(
                anxiety_score=7,
                stress_score=8,
                emotions=["pressured", "uncertain"],
            ),
            "insights": [
                "Family pressure is making career choices feel heavier.",
                "You care about being understood, not just winning.",
                "Your design interest keeps coming back strongly.",
            ],
            "suggestions": [
                "Write down three practical reasons design matters to you.",
                "Prepare one backup plan before the next conversation.",
                "Choose a calmer time before bringing it up again.",
            ],
            "is_crisis": False,
            "crisis_resources": None,
        }

    return None

def get_fallback_response(message: str, history: list[ChatMessage] | None = None) -> dict:
    history = history or []
    text = normalize_hinglish_text(message)
    crisis = is_crisis_message(message)
    last_user_message = get_last_user_message(history)
    vague_continuation = last_user_message and is_vague_continuation_message(message)
    use_hinglish = uses_hindi_or_hinglish(message)

    if crisis:
        if use_hinglish:
            reply = (
                "Mujhe glad hai tumne yeh bola. Please abhi is feeling ke saath akele mat raho. "
                "Kya tum kisi trusted person ko abhi call ya message kar sakte ho?"
            )
        else:
            reply = (
                "I'm really glad you told me. Please don't stay alone with this feeling right now. "
                "Can you call or message someone you trust?"
            )
        anxiety, stress, emotions = 9, 9, ["distressed", "unsafe"]
    elif is_positive_achievement_message(message):
        return get_positive_achievement_response(message)
    elif is_positive_relationship_message(message):
        return get_positive_relationship_response(message)
    elif is_positive_mood_message(message):
        return get_positive_mood_response(message)
    elif contextual_advice := get_contextual_advice_response(message, history):
        return contextual_advice
    elif contextual_response := get_contextual_fallback_response(message, history):
        return contextual_response
    elif any(word in text for word in ["exam", "study", "marks", "math", "assignment", "test"]):
        if use_hinglish:
            reply = (
                "Uff, exam pressure sach mein dimaag pe chadh jaata hai. "
                "Sabse zyada tension kis cheez ki ho rahi hai?"
            )
        else:
            reply = (
                "Exam pressure can really sit heavily on your mind. "
                "What part is stressing you out the most?"
            )
        anxiety, stress, emotions = 7, 8, ["anxious", "overwhelmed"]
    elif is_relationship_message(message):
        if use_hinglish:
            reply = (
                "Oof, yeh wali feeling chest mein atak jaati hai kabhi kabhi. "
                "Tum dono ke beech kya hua?"
            )
        else:
            reply = (
                "Oof, that kind of feeling can really sit in your chest. "
                "What happened between you two?"
            )
        anxiety, stress, emotions = 6, 7, ["sad", "hurt"]
    elif any(word in text for word in ["family", "parents", "pressure", "home"]):
        if use_hinglish:
            reply = (
                "Uff, close logon se pressure aaye toh aur exhausting lagta hai. "
                "Sabse zyada kis baat ka pressure hai?"
            )
        else:
            reply = (
                "Pressure from people close to you can feel especially exhausting. "
                "What are they pressuring you about the most?"
            )
        anxiety, stress, emotions = 7, 8, ["pressured", "stressed"]
    elif is_social_withdrawal_message(message):
        if use_hinglish:
            reply = (
                "Yeh wali feeling heavy lag sakti hai, jab kisi se baat karne ka mann hi na kare. "
                "Theek hai, solitude chahiye toh thoda space lo, bas apne aap ko bilkul cut off mat karna."
            )
        else:
            reply = (
                "That can feel heavy, when you don't want to talk to anyone at all. "
                "It's okay to take some space, just try not to cut yourself off completely."
            )
        anxiety, stress, emotions = 7, 7, ["withdrawn", "low", "overwhelmed"]
    elif any(word in text for word in ["happy", "excited", "passed", "won", "good news"]):
        if use_hinglish:
            reply = (
                "Arre wah, that's so good to hear. Properly batao, kya hua?"
            )
        else:
            reply = (
                "That's so good to hear. Tell me properly, what happened?"
            )
        anxiety, stress, emotions = 2, 2, ["happy", "excited"]
    elif any(word in text for word in ["sad", "upset", "cry", "crying", "lonely", "alone", "hurt"]):
        if use_hinglish:
            reply = (
                "Yeh sunke bura laga. Aaj kis cheez ne sabse zyada hurt kiya?"
            )
        else:
            reply = (
                "I'm sorry, that sounds like a rough place to be in. "
                "What hurt the most today?"
            )
        anxiety, stress, emotions = 6, 7, ["sad", "hurt"]
    elif any(word in text for word in ["anxious", "anxiety", "worried", "worry", "scared", "panic", "overwhelmed"]):
        if use_hinglish:
            reply = (
                "Uff, anxiety wali feeling body aur dimaag dono ko tired kar deti hai. "
                "Abhi sabse zyada darr kis baat ka lag raha hai?"
            )
        else:
            reply = (
                "Anxiety can make everything feel louder than it is. "
                "What are you most worried might happen?"
            )
        anxiety, stress, emotions = 8, 7, ["anxious", "worried"]
    elif any(word in text for word in ["stress", "stressed", "tension", "overload", "overloaded"]):
        if use_hinglish:
            reply = (
                "Uff, stress jab stack ho jaata hai toh sab kuch heavy lagne lagta hai. "
                "Sabse zyada load kis cheez ka hai?"
            )
        else:
            reply = (
                "That sounds like a lot sitting on you at once. "
                "What's adding the most pressure right now?"
            )
        anxiety, stress, emotions = 7, 8, ["stressed", "overwhelmed"]
    elif vague_continuation:
        if use_hinglish:
            reply = (
                "Haan, samajh raha hoon. Jo tum pehle bata rahe the usi ka yeh next part lag raha hai. "
                "Ismein abhi sabse zyada kya feel ho raha hai?"
            )
        else:
            reply = (
                "Yeah, I get you. This sounds connected to what you were saying earlier. "
                "What are you feeling most strongly about it right now?"
            )
        anxiety, stress, emotions = 5, 5, ["reflective"]
    else:
        if use_hinglish:
            reply = (
                "Main sun raha hoon. Jaise bhi mann mein aa raha hai, waise bol do. "
                "Aaj dimaag mein sabse zyada kya chal raha hai?"
            )
        else:
            reply = (
                "I'm listening. Say it however it comes to mind. "
                "What's been taking up the most space in your head today?"
            )
        anxiety, stress, emotions = 4, 4, ["neutral"]

    return {
        "reply": reply,
        "emotion_scores": EmotionScores(
            anxiety_score=anxiety,
            stress_score=stress,
            emotions=emotions,
        ),
        "insights": get_default_insights(emotions),
        "suggestions": get_default_suggestions(crisis),
        "is_crisis": crisis,
        "crisis_resources": CRISIS_RESOURCES if crisis else None,
    }

def get_ai_response(message: str, history: list[ChatMessage]) -> dict:
    contents = []
    trimmed_history = history[-MAX_HISTORY_CONTEXT:] if history else []
    gemini_history = get_valid_gemini_history(trimmed_history)

    for msg in gemini_history:
        role = "user" if msg.role == "user" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part(text=msg.content)]
        ))

    if contents and contents[-1].role == "user":
        contents[-1].parts.append(types.Part(text=message))
    else:
        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=message)]
        ))

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=build_system_instruction(trimmed_history),
                temperature=0.8,
                top_p=0.95,
            )
        )

        parsed = parse_gemini_json(response.text)

        anxiety = max(1, min(10, int(parsed.get("anxiety_score", 3))))
        stress = max(1, min(10, int(parsed.get("stress_score", 3))))
        crisis = bool(parsed.get("is_crisis", False)) or is_crisis_message(message)

        if crisis:
            anxiety = max(anxiety, 9)
            stress = max(stress, 9)
        elif is_social_withdrawal_message(message):
            anxiety = max(anxiety, 7)
            stress = max(stress, 7)
        elif is_positive_achievement_message(message):
            anxiety = min(anxiety, 2)
            stress = min(stress, 2)
            if any(term in parsed.get("reply", "").lower() for term in ["heavy", "fear of failing", "workload", "pressure"]):
                return get_positive_achievement_response(message)
        elif is_positive_relationship_message(message):
            anxiety = min(anxiety, 2)
            stress = min(stress, 2)
            if any(term in parsed.get("reply", "").lower() for term in ["hurt", "rough", "heavy", "what happened"]):
                return get_positive_relationship_response(message)
        elif is_positive_mood_message(message):
            anxiety = min(anxiety, 3)
            stress = min(stress, 3)

        reply = parsed.get("reply", "Hey, I'm listening. What's on your mind?")
        if not uses_hindi_or_hinglish(message) and uses_hindi_or_hinglish(reply):
            return get_fallback_response(message, trimmed_history)
        if trimmed_history and is_generic_restart_reply(reply):
            contextual_response = get_contextual_advice_response(message, trimmed_history)
            if contextual_response:
                return contextual_response

        emotions = parsed.get("emotions", ["neutral"])
        if not isinstance(emotions, list):
            emotions = ["neutral"]
        emotions = [
            str(emotion).strip()
            for emotion in emotions
            if str(emotion).strip()
        ] or ["neutral"]
        emotions = emotions[:5]
        insights = normalize_dashboard_items(
            parsed.get("insights"),
            get_default_insights(emotions),
            naturalize_insights=True,
        )
        suggestions = normalize_dashboard_items(
            parsed.get("suggestions"),
            get_default_suggestions(crisis),
        )

        return {
            "reply": reply,
            "emotion_scores": EmotionScores(
                anxiety_score=anxiety,
                stress_score=stress,
                emotions=emotions,
            ),
            "insights": insights,
            "suggestions": suggestions,
            "is_crisis": crisis,
            "crisis_resources": CRISIS_RESOURCES if crisis else None,
        }

    except Exception as e:
        print(f"[ERROR] Gemini API failed: {e}")
        return get_fallback_response(message, gemini_history)
