from textblob import TextBlob
from typing import Dict, List

# simple in-memory session store; replace with Redis for production
SESSIONS: Dict[str, List[dict]] = {}

def detect_sentiment(text: str) -> str:
    pol = TextBlob(text).sentiment.polarity
    if pol > 0.2: return "positive"
    if pol < -0.2: return "negative"
    return "neutral"

def append_session(user_id: str, role: str, content: str) -> int:
    if user_id not in SESSIONS:
        SESSIONS[user_id] = []
    SESSIONS[user_id].append({"role": role, "content": content})
    # keep last 10 turns
    if len(SESSIONS[user_id]) > 20:
        SESSIONS[user_id] = SESSIONS[user_id][-20:]
    return len(SESSIONS[user_id])

def convo_summary(user_id: str) -> str:
    hist = SESSIONS.get(user_id, [])[-6:]
    return "\n".join(f"{t['role']}: {t['content']}" for t in hist)
