"""Generate FAISS index from facet registry using SentenceTransformers.

Usage: python scripts/generate_faiss.py
"""
from __future__ import annotations
import os
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REG_PATH = Path(os.getenv("FACET_REGISTRY_PATH", ROOT / "data" / "processed" / "facet_registry.json"))
OUT_INDEX = Path(os.getenv("FAISS_INDEX_PATH", ROOT / "data" / "faiss_index.bin"))
VECTORS_NPY = Path(os.getenv("VECTORS_NPY", ROOT / "data" / "facet_vectors.npy"))


def build():
    if not REG_PATH.exists():
        raise FileNotFoundError("Facet registry not found. Run scripts/prepare_data.py first.")
    with REG_PATH.open("r", encoding="utf-8") as f:
        registry = json.load(f)

    texts = [f"{r['facet_name']}. {r.get('description','')}" for r in registry]

    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise RuntimeError("sentence-transformers is required to build embeddings") from e

    model = SentenceTransformer(model_name)
    vecs = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    # Write numpy vectors
    VECTORS_NPY.parent.mkdir(parents=True, exist_ok=True)
    np.save(VECTORS_NPY, vecs)

    # Build FAISS index
    try:
        import faiss
    except Exception as e:
        raise RuntimeError("faiss-cpu is required to build index") from e

    dim = vecs.shape[1]
    index = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(vecs)
    index.add(vecs)
    OUT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(OUT_INDEX))
    print(f"Saved FAISS index to {OUT_INDEX} and vectors to {VECTORS_NPY}")


if __name__ == "__main__":
    build()
