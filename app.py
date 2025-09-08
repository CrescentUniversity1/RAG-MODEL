"""
Streamlit UI for CrescentBot (RAG-enabled)
"""

import os
import streamlit as st
from utils.rag_pipeline import RAGIndex, Generator, RAGPipeline, ingest_json_files
from utils.preprocess import preprocess_text
from utils.memory import init_memory
from utils.log_utils import log_query
from utils.greetings import is_greeting, greeting_responses, is_social_trigger, social_response
from utils.course_query import extract_course_query, get_courses_for_query
from utils.tone import dynamic_prefix, dynamic_not_found
from utils.rewrite import rewrite_followup

INDEX_DIR = "RAG-MODEL/index"
DATA_DIR = "RAG-MODEL/data"

# Initialize session state
init_memory()

# Load course data for context enhancement
@st.cache_resource(show_spinner=True)
def load_course_data():
    try:
        with open(f"{DATA_DIR}/course_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Course data not found at {DATA_DIR}/course_data.json")
        return []

# Load or build RAG index
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
course_data = load_course_data()

# Streamlit UI
st.set_page_config(page_title="CrescentBot RAG", layout="wide")
st.title("🌙 CrescentBot (RAG-enabled)")

# Display warning if no documents were indexed
if not pipeline.index.metadata:
    st.warning("No documents were indexed. Please ensure course_data.json and crescent_qa.json are in RAG-MODEL/data/ and contain valid data.")

# Display chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if query := st.chat_input("Ask me anything about Crescent courses..."):
    st.session_state["messages"].append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.spinner("Thinking..."):
        # Handle greetings and social triggers
        if is_greeting(query):
            response = greeting_responses()
        elif is_social_trigger(query):
            response = social_response(query)
        else:
            # Preprocess query
            processed_query = preprocess_text(query, debug=True)
            # Rewrite query with context from last query
            processed_query = rewrite_followup(processed_query, st.session_state["last_query_info"])
            # Extract course-specific query info for context
            query_info = extract_course_query(processed_query)
            st.session_state["last_query_info"] = query_info

            # Enhance query with course-specific info
            if query_info["department"] and query_info["level"] and query_info["semester"]:
                processed_query += f" for {query_info['department']} {query_info['level']} level {query_info['semester']} semester"

            # Use RAG pipeline
            rag_out = pipeline.answer(processed_query)
            if rag_out["answer"] and rag_out["retrieved"]:
                response = f"{dynamic_prefix()} {rag_out['answer']}"
                log_query(query, max([score for _, score in rag_out["retrieved"]], default=0.0))
            else:
                response = dynamic_not_found()
                log_query(query, 0.0)

        st.session_state["messages"].append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
            if "rag_out" in locals() and rag_out["retrieved"]:
                with st.expander("Show supporting passages"):
                    for md, score in rag_out["retrieved"]:
                        st.markdown(f"**{md['source']}** — {md['id']} (score={score:.3f})\n\n{md['text']}")
