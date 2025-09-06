import os, json, pathlib, re
from typing import List, Tuple, Dict
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer, util
from pypdf import PdfReader

DATA_DIR = pathlib.Path("data")
INDEX_PATH = DATA_DIR / "index.faiss"
META_PATH = DATA_DIR / "meta.json"
MODEL_CACHE = DATA_DIR / "model_cache"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", 0.45))
TOP_K_DEFAULT = int(os.getenv("TOP_K", 3))

_model = None
_index = None
_meta: List[Dict] = []

# ---------- Loading & Helpers ----------

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL, cache_folder=str(MODEL_CACHE))
    return _model


def _chunk_text(text: str, max_tokens: int = 400, overlap: int = 60) -> List[str]:
    # simple token-ish chunk by sentence; adjust as needed
    sents = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks, buf = [], []
    size = 0
    for s in sents:
        ln = len(s.split())
        if size + ln > max_tokens and buf:
            chunks.append(" ".join(buf))
            buf, size = [], 0
        buf.append(s)
        size += ln
    if buf:
        chunks.append(" ".join(buf))
    # add overlap
    out = []
    for i, c in enumerate(chunks):
        prev_tail = chunks[i-1].split()[-overlap:] if i>0 else []
        out.append((" ".join(prev_tail) + " " + c).strip())
    return out


def _read_file(path: pathlib.Path) -> List[Tuple[str, Dict]]:
    """Return list of (chunk, meta). Supports .txt/.md/.pdf and knowledge.json keys."""
    items: List[Tuple[str, Dict]] = []
    if path.suffix.lower() in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for chunk in _chunk_text(text):
            items.append((chunk, {"title": path.name, "source": str(path)}))
    elif path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        pages = []
        for i, p in enumerate(reader.pages):
            try:
                pages.append((p.extract_text() or "").strip())
            except Exception:
                pages.append("")
        for i, text in enumerate(pages):
            for chunk in _chunk_text(text):
                items.append((chunk, {"title": f"{path.name} – p.{i+1}", "source": f"{path}#page={i+1}"}))
    elif path.name == "knowledge.json":
        kb = json.loads(path.read_text(encoding="utf-8"))
        for cat, data in kb.items():
            if isinstance(data, dict):
                for key, val in data.items():
                    txt = f"[{cat} → {key}] {val}"
                    for chunk in _chunk_text(txt, max_tokens=120):
                        items.append((chunk, {"title": f"KB:{cat}/{key}", "source": str(path)}))
            else:
                for chunk in _chunk_text(str(data), max_tokens=120):
                    items.append((chunk, {"title": f"KB:{cat}", "source": str(path)}))
    return items


def build_index() -> None:
    global _index, _meta
    model = get_model()
    texts: List[str] = []
    metas: List[Dict] = []

    # gather inputs
    if (DATA_DIR / "knowledge.json").exists():
        for chunk, meta in _read_file(DATA_DIR / "knowledge.json"):
            texts.append(chunk); metas.append(meta)
    docs_dir = DATA_DIR / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    for p in docs_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".txt", ".md", ".pdf"}:
            for chunk, meta in _read_file(p):
                texts.append(chunk); metas.append(meta)

    if not texts:
        raise RuntimeError("No documents found in data/. Add knowledge.json or files in data/docs/")

    emb = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)

    # save
    DATA_DIR.mkdir(exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    META_PATH.write_text(json.dumps(metas, ensure_ascii=False, indent=2))

    _index, _meta = index, metas


def load_index():
    global _index, _meta
    if _index is None:
        if not INDEX_PATH.exists() or not META_PATH.exists():
            build_index()
        else:
            _index = faiss.read_index(str(INDEX_PATH))
            _meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    return _index, _meta


def retrieve(query: str, top_k: int = None):
    index, metas = load_index()
    model = get_model()
    top_k = top_k or TOP_K_DEFAULT
    q = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    D, I = index.search(q, top_k)
    results = []
    for rank, (score, idx) in enumerate(zip(D[0].tolist(), I[0].tolist())):
        if idx == -1: continue
        if score < SIM_THRESHOLD: continue
        m = metas[idx]
        results.append({
            "id": rank + 1,
            "score": float(score),
            "title": m.get("title", "Document"),
            "source": m.get("source", ""),
            "snippet": m.get("snippet", ""),
            "meta": m,
        })
    return results
