# memory.py

import streamlit as st

def init_memory():
    if "last_query_info" not in st.session_state:
        st.session_state["last_query_info"] = {}
    if "chat" not in st.session_state:
        st.session_state["chat"] = []
    if "bot_greeted" not in st.session_state:
        st.session_state["bot_greeted"] = False
