import random
import re

# --- Greeting Triggers ---
GREETING_KEYWORDS = [
    "hello", "hi", "hey", "yo", "howdy", "hiya", "sup", "what's up",
    "good morning", "good afternoon", "good evening", "greetings"
]

GREETING_RESPONSES = [
    "Hello! 👋 How can I assist you with Crescent University today?",
    "Hi there! 😊 What would you like to know about Crescent University?",
    "Hey! 👋 Feel free to ask me anything related to Crescent University.",
    "Greetings! 🤝 I’m here to help with your Crescent University questions.",
    "Yo! 👋 Ready to chat about Crescent University?",
    "Hiya! 🙋 Let me know what you need help with at Crescent University.",
    "Howdy! 🤠 I'm your friendly assistant for all things Crescent University.",
    "Good to see you! 🌟 Got any questions about Crescent University?"
]

# --- Small Talk + Emotional Patterns ---
SOCIAL_PATTERNS = {
    r"\bhow are you\b": [
        "I'm doing great, thank you! 😊 How can I help you today?",
        "Feeling sharp and ready to assist! ⚡",
        "All good here—excited to help you out! 🤖"
    ],
    r"\bwhat(?:'s| is) your name\b": [
        "You can call me CrescentBot 🤖, your helpful university assistant.",
        "I go by CrescentBot! I know quite a lot about Crescent University. 🎓"
    ],
    r"\btell me about yourself\b": [
        "I'm CrescentBot, built to assist students and staff with everything about Crescent University! 💬",
        "I’m trained to answer your questions about courses, departments, admissions and more! 🎓"
    ],
    r"\bwho (are|r) you\b": [
        "I'm CrescentBot, your AI guide to Crescent University. 🎓 Ask me anything!",
        "I’m your virtual assistant, here to help with all things Crescent University!"
    ],
    r"\bthank(s| you)\b": [
        "You're very welcome! 😊",
        "Anytime! Let me know if you have more questions. 🙌",
        "Glad to help! 👍"
    ],
    r"\bgood (job|bot|work)\b": [
        "Thank you! 🤖 I’m here to help anytime!",
        "I appreciate that! 😊",
        "Yay! I'm glad I could help. 💙"
    ],
    r"\bi(?:'m| am)?\s+(confused|lost|not sure)\b": [
        "No worries — I'm here to help. Can you please clarify what you're trying to find? 🤔",
        "It’s okay to feel confused! Just ask me anything about Crescent University. 💡"
    ],
    r"\bi(?:'m| am)?\s+(sad|tired|bored|upset)\b": [
        "I’m here if you need someone to talk to. Want to explore some Crescent Uni resources together? 💙",
        "Sorry you're feeling that way. Let's focus on something helpful or interesting! 😊"
    ],
    r"\bi (don't )?understand\b": [
        "Let me try to explain it better. What exactly would you like me to break down? 🧠",
        "Totally fine! Please rephrase or point out where you’re stuck. I’ve got you. 💪"
    ],
    r"\bthat (wasn't|isn't|is not) helpful\b": [
        "Oops! Let me try that again. Could you be more specific so I can assist better? 🙏",
        "Thanks for the feedback. I’ll do my best to clarify or find a better answer. 🔍"
    ],
    r"\bi'm happy\b": [
        "Yay! That’s always great to hear 😄 Anything I can do to make your day even better?",
        "Awesome! Let's keep the good vibes going! 🌟"
    ]
}

# --- Detection Functions ---
def is_greeting(text):
    text = text.lower()
    return any(re.search(rf"\b{kw}\b", text) for kw in GREETING_KEYWORDS)

def greeting_responses():
    return random.choice(GREETING_RESPONSES)

def is_social_trigger(text):
    text = text.lower()
    for pattern in SOCIAL_PATTERNS:
        if re.search(pattern, text):
            return True
    return False

def social_response(text):
    text = text.lower()
    for pattern, responses in SOCIAL_PATTERNS.items():
        if re.search(pattern, text):
            return random.choice(responses)
    return None
