import httpx
from app.core.config import settings

TELEGRAM_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

async def send_crisis_alert(
    chat_id: str,
    contact_name: str,
    session_id: str,
    user_name: str | None = None,
) -> bool:
    try:
        user_label = user_name.strip() if user_name and user_name.strip() else "Someone"
        message = f"""
*MindEase Crisis Alert*

Dear *{contact_name}*,

*{user_label}* listed you as their emergency contact and may be in emotional distress or crisis right now.

Please reach out to *{user_label}* *immediately* and check in on them.

If you believe they are in immediate danger, call emergency services (*112*).

---
*Crisis Helplines (India):*
- iCall: 9152987821
- Vandrevala Foundation: 1860-2662-345 (24/7)
- AASRA: 9820466627
---
_Session Ref: {session_id}_
_Sent automatically by MindEase_
        """

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                },
            )

        if response.status_code == 200:
            print(f"Crisis alert sent to Telegram chat {chat_id}")
            return True

        print(f"Telegram error: {response.text}")
        return False

    except Exception as e:
        print(f"Failed to send alert: {str(e)}")
        return False
