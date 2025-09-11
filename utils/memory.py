# memory.py
import streamlit as st
import sqlite3
from datetime import datetime

def init_memory():
    """Initialize short-term memory in session_state."""
    if "last_query_info" not in st.session_state:
        st.session_state["last_query_info"] = {
            "department": None,
            "level": None,
            "semester": None,
            "keywords": [],
            "sentiment": None
        }
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "bot_greeted" not in st.session_state:
        st.session_state["bot_greeted"] = False

def init_database(db_path="RAG-MODEL/user_history.db"):
    """Initialize SQLite database for long-term memory."""
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_query TEXT,
            response TEXT,
            department TEXT,
            level TEXT,
            semester TEXT,
            sentiment TEXT,
            keywords TEXT
        )""")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Failed to initialize database: {e}")
    finally:
        conn.close()

def save_interaction(query, response, query_info, sentiment, db_path="RAG-MODEL/user_history.db"):
    """Save a user interaction to the long-term memory database."""
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        c = conn.cursor()
        keywords = " ".join(query_info.get("keywords", [])) if query_info.get("keywords") else ""
        c.execute("""INSERT INTO history (timestamp, user_query, response, department, level, semester, sentiment, keywords)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), query, response,
                   query_info.get("department"), query_info.get("level"), query_info.get("semester"),
                   sentiment, keywords))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Failed to save interaction: {e}")
    finally:
        conn.close()

def get_user_history(limit=10, db_path="RAG-MODEL/user_history.db"):
    """Retrieve recent user interactions from long-term memory."""
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT timestamp, user_query, response, department, level, semester, sentiment, keywords FROM history ORDER BY timestamp DESC LIMIT ?", (limit,))
        history = c.fetchall()
        conn.close()
        return [{"timestamp": h[0], "query": h[1], "response": h[2], "department": h[3], "level": h[4], 
                 "semester": h[5], "sentiment": h[6], "keywords": h[7].split() if h[7] else []} for h in history]
    except sqlite3.Error as e:
        print(f"Failed to retrieve history: {e}")
        return []

def get_relevant_context(limit=3, db_path="RAG-MODEL/user_history.db"):
    """Get relevant context from long-term memory to enhance RAG queries."""
    history = get_user_history(limit=limit, db_path=db_path)
    if not history:
        return None
    context = {
        "departments": list(set(h["department"] for h in history if h["department"])),
        "levels": list(set(h["level"] for h in history if h["level"])),
        "semesters": list(set(h["semester"] for h in history if h["semester"])),
        "keywords": list(set(kw for h in history for kw in h["keywords"] if kw)),
        "sentiments": list(set(h["sentiment"] for h in history if h["sentiment"]))
    }
    return context
