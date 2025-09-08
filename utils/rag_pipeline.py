"""
RAG Pipeline for CrescentBot

- Ingests JSON knowledge files (course_data.json, crescent_qa.json)
- Splits into passages
- Embeds with SentenceTransformer
- Indexes with FAISS
- Retrieves top passages
- Generates answers with Flan-T5
- Returns answer + used passages

Requirements:
    pip install sentence-transformers faiss-cpu transformers accelerate
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


# --------------------------- Text splitting
def split_text_into_passages(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")
    passages = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = start + chunk_size
        passages.append(text[start:end].strip())
        start = max(start + chunk_size - overlap, end)
    return [p for p in passages if p]


# --------------------------- Ingestion
def ingest_json_files(data_dir: str) -> List[Dict]:
    """Load course_data.json and crescent_qa.json into passage chunks."""
    docs = []
    data_dir_path = Path(data_dir)
    if not data_dir_path.exists():
        print(f"Data directory does not exist: {data_dir}")
        return docs
    for fname in ["course_data.json", "crescent_qa.json"]:
        path = data_dir_path / fname
        print(f"Checking file: {path}")  # Debug
        if not path.exists():
            print(f"File not found: {path}")
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {path}: {e}")
            continue
        if not data:
            print(f"No data in {path}")
            continue
        if isinstance(data, dict):
            items = data.items()
        elif isinstance(data, list):
            items = enumerate(data)
        else:
            print(f"Unsupported data type in {path}: {type(data)}")
            continue
        for key, val in items:
            text = str(val)
            passages = split_text_into_passages(text)
            print(f"File {fname}: {len(passages)} passages from key {key}")  # Debug
            for i, p in enumerate(passages):
                docs.append({
                    "id": f"{fname}_{key}_{i}",
                    "source": fname,
                    "text": p,
                })
    print(f"Total documents loaded: {len(docs)}")  # Debug
    return docs


# --------------------------- Embedding & Indexing
class RAGIndex:
    def __init__(self, embed_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embedder = SentenceTransformer(embed_model_name)
        self.index: Optional[faiss.IndexFlatIP] = None
        self.metadata: List[Dict] = []

    def build(self, docs: List[Dict]):
        if not docs:
            print("Warning: No documents found for indexing. Initializing empty index.")
            self.metadata = []
            self.index = faiss.IndexFlatIP(384)  # Default dimension for all-MiniLM-L6-v2
            return
        texts = [d["text"] for d in docs]
        self.metadata = docs
        embs = self.embedder.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        faiss.normalize_L2(embs)
        d = embs.shape[1]
        self.index = faiss.IndexFlatIP(d)
        self.index.add(embs)

    def save(self, path: str):
        os.makedirs(path, exist_ok=True)
        faiss.write_index(self.index, os.path.join(path, "index.faiss"))
        with open(os.path.join(path, "metadata.pkl"), "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self, path: str):
        self.index = faiss.read_index(os.path.join(path, "index.faiss"))
        with open(os.path.join(path, "metadata.pkl"), "rb") as f:
            self.metadata = pickle.load(f)

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        q_emb = self.embedder.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(q_emb)
        D, I = self.index.search(q_emb, top_k)
        result = []
        for score, idx in zip(D[0], I[0]):
            result.append((self.metadata[int(idx)], float(score)))
        return result


# --------------------------- Generator
PROMPT_TMPL = (
    "You are CrescentBot, a helpful assistant. Use the provided context to answer.\n"
    "If context lacks the answer, say you don't know.\n\n"
    "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
)

class Generator:
    def __init__(self, model_name: str = "google/flan-t5-base", device: int = -1):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        try:
            import torch
            if device >= 0:
                self.model = self.model.to(device)
        except Exception:
            pass

    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.0) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=temperature > 0.0,
            temperature=temperature,
            top_p=0.95,
            num_beams=2 if temperature == 0.0 else 1,
        )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)


# --------------------------- Pipeline
class RAGPipeline:
    def __init__(self, index: RAGIndex, generator: Generator):
        self.index = index
        self.generator = generator

    def construct_context(self, retrieved: List[Tuple[Dict, float]], max_passages: int = 5) -> str:
        ctx_parts = []
        for i, (meta, score) in enumerate(retrieved[:max_passages]):
            ctx_parts.append(f"[{i+1}] {meta['source']}\n{meta['text']}")
        return "\n\n".join(ctx_parts)

    def answer(self, query: str, top_k: int = 10, max_passages: int = 5) -> Dict:
        retrieved = self.index.retrieve(query, top_k)
        context = self.construct_context(retrieved, max_passages)
        prompt = PROMPT_TMPL.format(context=context, question=query)
        answer = self.generator.generate(prompt)
        return {
            "answer": answer,
            "retrieved": retrieved[:max_passages],
        }


# --------------------------- CLI build & test
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="RAG-MODEL/data")
    parser.add_argument("--index_dir", type=str, default="RAG-MODEL/index")
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    idx = RAGIndex()
    if not os.path.exists(args.index_dir) or args.rebuild:
        docs = ingest_json_files(args.data_dir)
        idx.build(docs)
        idx.save(args.index_dir)
    else:
        idx.load(args.index_dir)

    gen = Generator()
    pipeline = RAGPipeline(idx, gen)

    while True:
        q = input("Q: ")
        if q.lower().strip() in ("quit", "exit"):
            break
        out = pipeline.answer(q)
        print("Answer:", out["answer"])
        for md, score in out["retrieved"]:
            print(f"- {md['id']} (score={score:.3f})")
