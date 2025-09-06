# Usage: python -m app.ingest
from .rag import build_index

if __name__ == "__main__":
    print("Building FAISS index from data/ ...")
    build_index()
    print("✅ Index built: data/index.faiss, data/meta.json")
