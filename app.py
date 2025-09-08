# File: CRESCENTBOT/app.py
"""
Streamlit UI for CrescentBot (RAG-enabled)

This version replaces the old embedding/search backend with the new RAG pipeline.
"""

import os
import streamlit as st

from utils.rag_pipeline import RAGIndex, Generator, RAGPipeline, ingest_json_files

INDEX_DIR = "CRESCENTBOT/index"
DATA_DIR = "CRESCENTBOT/data"

# --------------------------- Load or build RAG index
@st.cache_resource(show_spinner=True)
def load_pipeline():
    idx = RAGIndex()
    if not os.path.exists(INDEX_DIR):
        st.info("Building FAISS index from JSON knowledge base... this may take a while.")
        docs = ingest_json_files(DATA_DIR)
        idx.build(docs)
        idx.save(INDEX_DIR)
    else:
        idx.load(INDEX_DIR)
    gen = Generator()
    pipeline = RAGPipeline(idx, gen)
    return pipeline

pipeline = load_pipeline()

# --------------------------- Streamlit UI
st.set_page_config(page_title="CrescentBot RAG", layout="wide")
st.title("🌙 CrescentBot (RAG-enabled)")

# Chat session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if query := st.chat_input("Ask me anything about Crescent courses..."):
    st.session_state["messages"].append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.spinner("Thinking..."):
        out = pipeline.answer(query)
        answer = out["answer"]

    st.session_state["messages"].append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

        with st.expander("Show supporting passages"):
            for md, score in out["retrieved"]:
                st.markdown(f"**{md['source']}** — {md['id']} (score={score:.3f})\n\n{md['text']}")
