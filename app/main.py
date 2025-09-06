import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
from .models import ChatRequest, ChatResponse, Source, UpsertDoc
from .rag import retrieve, build_index, DATA_DIR
from .utils import detect_sentiment, append_session, convo_summary
from .prompts import SYSTEM_PROMPT, ANSWER_TEMPLATE
import orjson

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "text-davinci-003")
client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="University Chatbot – RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/reindex")
def reindex():
    build_index()
    return {"status": "reindexed"}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: C
