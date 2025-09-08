import random

def dynamic_prefix():
    options = [
        "Here's what I found for you 😊:",
        "Let’s break it down 🔍:",
        "Check this out 📘:",
        "I got you! 👇",
        "✨ Here's something helpful:",
    ]
    return random.choice(options)

def dynamic_not_found():
    options = [
        "😕 I couldn’t find an answer to that. Try rephrasing it?",
        "🤔 That one stumped me. Can you ask another way?",
        "I’m not sure I have that info yet. Ask something else?",
        "Sorry, I couldn’t match that to anything I know.",
    ]
    return random.choice(options)
