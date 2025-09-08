import json
import pandas as pd
from sentence_transformers import SentenceTransformer
import torch

def load_model(model_name="all-MiniLM-L6-v2"):
    """Load SentenceTransformer model"""
    return SentenceTransformer(model_name)

def load_dataset(path="data/crescent_qa.json"):
    """Load Q&A dataset from JSON into pandas DataFrame"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)

def compute_question_embeddings(questions, model):
    """Compute sentence embeddings for a list of questions"""
    return model.encode(questions, convert_to_tensor=True, show_progress_bar=True)
