"""
Streamlit UI for CrescentBot (Fully RAG-enabled with Emotion Detection and Memory)
"""

import os
import streamlit as st
from textblob import TextBlob
from utils.rag_pipeline import RAGIndex, Generator, RAGPipeline, ingest_json_files
from utils.preprocess import preprocess_text
from utils.memory import init_memory, init_database, save_interaction, get_relevant_context
from utils.log_utils import log_query
from utils.greetings import is_greeting, greeting_responses, is_social_trigger, social_response
from utils.course_query import extract_course_query
from utils.tone import dynamic_prefix, dynamic_not_found
from utils.rewrite import rewrite_followup

INDEX_DIR = "RAG-MODEL/index"
DATA_DIR = "RAG-MODEL/data"

# Initialize memory and database
init_memory()
init_database()

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

# Function for emotion detection
def detect_emotion(query):
    blob = TextBlob(query)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return "positive"
    elif polarity < -0.1:
        return "negative"
    return "neutral"

# Streamlit UI
st.set_page_config(page_title="CrescentBot RAG", layout="wide")
st.title("🌙 CrescentBot (Fully RAG-enabled with Emotion Detection)")

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
        # Detect emotion
        sentiment = detect_emotion(query)

        # Handle greetings and social triggers (rule-based)
        if is_greeting(query):
            response = greeting_responses()
        elif is_social_trigger(query):
            response = social_response(query)
        else:
            # Preprocess query
            processed_query = preprocess_text(query, debug=True)
            # Rewrite query with short-term memory context
            processed_query = rewrite_followup(processed_query, st.session_state["last_query_info"])
            # Extract course-specific query info
            query_info = extract_course_query(processed_query)
            # Add keywords and sentiment to query_info
            query_info["keywords"] = processed_query.split()[:5]  # Top 5 keywords
            query_info["sentiment"] = sentiment
            st.session_state["last_query_info"] = query_info

            # Enhance query with short-term and long-term context
            context = get_relevant_context(limit=3)
            if context:
                if context["departments"]:
                    processed_query += f" related to {', '.join(context['departments'])}"
                if context["keywords"]:
                    processed_query += f" including keywords {', '.join(context['keywords'][:3])}"

            # Add course-specific context
            if query_info["department"]:
                processed_query += f" in {query_info['department']} department"
            if query_info["level"]:
                processed_query += f" for {query_info['level']} level"
            if query_info["semester"]:
                processed_query += f" in {query_info['semester']} semester"

            # Use RAG pipeline for retrieval and generation
            rag_out = pipeline.answer(processed_query)
            max_score = max([score for _, score in rag_out["retrieved"]], default=0.0)
            if rag_out["answer"] and rag_out["retrieved"] and max_score >= 0.6:
                prefix = dynamic_prefix()
                if sentiment == "negative":
                    prefix = "I'm sorry you're feeling that way—let's see if this helps: 😊 "
                elif sentiment == "positive":
                    prefix = "I'm glad you're feeling good! Here's what I found: 🌟 "
                response = f"{prefix}{rag_out['answer']}"
                log_query(query, max_score)
            else:
                response = dynamic_not_found()
                log_query(query, 0.0)

            # Save interaction to long-term memory
            save_interaction(query, response, query_info, sentiment)

    st.session_state["messages"].append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
        if rag_out["retrieved"]:
            with st.expander("Show supporting passages"):
                for md, score in rag_out["retrieved"]:
                    st.markdown(f"**{md['source']}** — {md['id']} (score={score:.3f})\n\n{md['text']}")
