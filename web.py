import streamlit as st
import os
import uuid
import openai
from dotenv import load_dotenv

from utils.embedding import load_model, load_dataset, compute_question_embeddings
from utils.preprocess import preprocess_text
from utils.search import find_response
from utils.memory import init_memory
from utils.log_utils import log_query
from utils.greetings import is_greeting, greeting_responses, is_social_trigger, social_response
from utils.course_query import extract_course_query  # for extracting level/semester

# --- Load Environment Variables ---
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Page Settings ---
st.set_page_config(page_title="Crescent University Chatbot", page_icon="🎓")

# --- Initialize Session State & Memory ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "related_questions" not in st.session_state:
    st.session_state.related_questions = []
if "last_department" not in st.session_state:
    st.session_state.last_department = None

init_memory()

# --- Load Model & Dataset ---
@st.cache_resource
def load_bot_resources():
    model = load_model()
    data = load_dataset()
    embeddings = compute_question_embeddings(data["question"].tolist(), model)
    return model, data, embeddings

model, dataset, question_embeddings = load_bot_resources()

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 💬 CrescentBot")
    if st.button("🧹 Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.related_questions = []
        st.session_state.last_department = None
        st.session_state.last_query_info = {}
        st.rerun()

# --- Styles ---
st.markdown("""
<style>
    html, body, .stApp { font-family: 'Segoe UI', sans-serif; }
    h1 { color: #004080; }
    .chat-message-user {
        background-color: #d6eaff;
        padding: 12px;
        border-radius: 15px;
        margin-bottom: 10px;
        margin-left: auto;
        max-width: 75%;
        font-weight: 550;
        color: #000;
    }
    .chat-message-assistant {
        background-color: #f5f5f5;
        padding: 12px;
        border-radius: 15px;
        margin-bottom: 10px;
        margin-right: auto;
        max-width: 75%;
        font-weight: 600;
        color: #000;
    }
    .related-question {
        background-color: #e6f2ff;
        padding: 8px 12px;
        margin: 6px 6px 6px 0;
        display: inline-block;
        border-radius: 10px;
        font-size: 0.9rem;
        cursor: pointer;
    }
    .department-label {
        font-size: 0.8rem;
        color: #004080;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("🎓 Crescent University Chatbot")

# --- Display Chat History ---
for msg in st.session_state.chat_history:
    css_class = "chat-message-user" if msg["role"] == "user" else "chat-message-assistant"
    with st.chat_message(msg["role"]):
        st.markdown(f'<div class="{css_class}">{msg["content"]}</div>', unsafe_allow_html=True)
        if msg["role"] == "assistant" and st.session_state.last_department:
            st.markdown(f'<div class="department-label">Department: {st.session_state.last_department}</div>', unsafe_allow_html=True)

# --- Show Previous Query Context ---
if st.session_state["last_query_info"]:
    last = st.session_state["last_query_info"]
    if last.get("department") or last.get("level"):
        st.markdown(
            f"<div style='color:gray;font-size:0.85rem;'>💡 You recently asked about <b>{last.get('level', '...')}</b> in <b>{last.get('department', 'a department')}</b>.</div>",
            unsafe_allow_html=True
        )

# --- Define follow-up detection ---
def is_follow_up(text):
    triggers = ["what about", "how about", "and", "also", "okay", "now", "then", "continue", "next"]
    return any(phrase in text.lower() for phrase in triggers)

# --- User Input ---
user_input = st.chat_input("Ask me anything about Crescent University...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # ✅ Greeting check
    if is_greeting(user_input):
        response = greeting_responses()
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

    # --- Extract query info ---
    query_info = extract_course_query(user_input)
    extracted_level = query_info.get("level")
    extracted_semester = query_info.get("semester")
    extracted_department = query_info.get("department")

    # --- If follow-up, enrich query with memory ---
    if is_follow_up(user_input) and st.session_state["last_query_info"]:
        prev = st.session_state["last_query_info"]
        enriched_input = f"{user_input} in {prev.get('department', '')}"
        if prev.get("level") and "level" not in user_input:
            enriched_input += f" {prev['level']} level"
        if prev.get("semester") and "semester" not in user_input:
            enriched_input += f", {prev['semester']} semester"
        cleaned_input = preprocess_text(enriched_input)
    else:
        cleaned_input = preprocess_text(user_input)

    # --- Try direct match first ---
    matched_row = dataset[dataset['question'].str.lower() == cleaned_input.lower()]
    if not matched_row.empty:
        response = matched_row.iloc[0]['answer']
        department = extracted_department
        related = []
        score = 1.0
    else:
        response, department, score, related = find_response(cleaned_input, dataset, question_embeddings)

        # --- GPT-4 fallback ---
        if score < 0.65 or not response.strip():
            try:
                gpt_reply = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for Crescent University. Answer only based on the university's academic programs, departments, and policies."},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                response = gpt_reply['choices'][0]['message']['content']
                department = extracted_department
                related = []
                response += "\n\n🧠 _This response was generated by GPT-4 fallback._"
            except Exception as e:
                response = "⚠️ Sorry, I'm currently unable to fetch a response from GPT-4."
                print(f"GPT-4 Fallback Error: {e}")

    # --- Store to memory ---
    st.session_state["last_query_info"] = {
        "query": user_input,
        "response": response,
        "department": extracted_department or department,
        "level": extracted_level,
        "semester": extracted_semester,
        "score": score
    }

    st.session_state.chat_history.append({"role": "assistant", "content": response})
    st.session_state.related_questions = related
    st.session_state.last_department = department

    log_query(user_input, score)
    st.rerun()

# --- Follow-Up Suggestions ---
if st.session_state.related_questions:
    st.markdown("#### 💡 You might also ask:")
    for i, q in enumerate(st.session_state.related_questions):
        if st.button(q, key=f"related_{i}", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": q})
            response, department, score, related = find_response(q, dataset, question_embeddings)

            if score < 0.65 or not response.strip():
                try:
                    gpt_reply = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant for Crescent University. Answer only based on the university's academic programs, departments, and policies."},
                            {"role": "user", "content": q}
                        ],
                        temperature=0.7,
                        max_tokens=300
                    )
                    response = gpt_reply['choices'][0]['message']['content']
                    department = None
                    related = []
                    response += "\n\n🧠 _This response was generated by GPT-4 fallback._"
                except Exception as e:
                    response = "⚠️ Sorry, I'm currently unable to fetch a response from GPT-4."
                    print(f"GPT-4 Related Fallback Error: {e}")

            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.session_state.related_questions = related
            st.session_state.last_department = department
            log_query(q, score)
            st.rerun()
