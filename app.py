"""
Streamlit UI for CrescentBot (RAG-enabled)
"""

import os
import streamlit as st

from utils.rag_pipeline import RAGIndex, Generator, RAGPipeline, ingest_json_files
from utils.embedding import load_model, load_dataset, compute_question_embeddings
from utils.preprocess import preprocess_text
from utils.search import find_response
from utils.memory import init_memory
from utils.log_utils import log_query
from utils.greetings import is_greeting, greeting_responses, is_social_trigger, social_response
from utils.course_query import extract_course_query  # for extracting level/semester

INDEX_DIR = "RAG-MODEL/index"
DATA_DIR = "RAG-MODEL/data"

# --------------------------- Load or build RAG index
@st.cache_resource(show_spinner=True)
def load_pipeline():
    idx = RAGIndex()
    if not os.path.exists(INDEX_DIR):
        st.info("Building FAISS index from JSON knowledge base... this may take a while.")
        docs = ingest_json_files(DATA_DIR)
        if not docs:
            st.error(f"No documents found in {DATA_DIR}. Please ensure course_data.json and crescent_qa.json exist and contain valid data.")
        else:
            st.write(f"Loaded {len(docs)} documents from {DATA_DIR}")
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

# Display warning if no documents were indexed
if not pipeline.index.metadata:
    st.warning("No documents were indexed. Please ensure course_data.json and crescent_qa.json are in RAG-MODEL/data/ and contain valid data.")

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
