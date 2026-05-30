from __future__ import annotations
from typing import List, Dict, Optional
import json
from pathlib import Path
from app.retrieval.embeddings import load_embedding_model, embed_texts
from app.retrieval.faiss_index import load_index, search_index
from app.core.config import settings


class Retriever:
    def __init__(self, registry_path: Optional[str] = None, index_path: Optional[str] = None, model_name: Optional[str] = None):
        self.registry_path = registry_path or settings.FACET_REGISTRY_PATH
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._load_registry()
        self._load_index()

    def _load_registry(self):
        p = Path(self.registry_path)
        if not p.exists():
            self.registry = []
        else:
            with p.open("r", encoding="utf-8") as f:
                self.registry = json.load(f)

    def _load_index(self):
        try:
            self.index = load_index(self.index_path)
            self.emb_model = load_embedding_model(self.model_name)
        except Exception:
            self.index = None
            self.emb_model = None

    def retrieve(self, conversation: str, top_k: int = 10, category_filter: Optional[List[str]] = None) -> List[Dict]:
        if not self.index or not self.emb_model:
            # fallback to simple substring match
            results = [f for f in self.registry if (not category_filter) or (f.get("category") in category_filter)]
            return results[:top_k]

        vec = embed_texts(self.emb_model, [conversation])
        D, I = search_index(self.index, vec, top_k)
        res = []
        for idx in I[0]:
            if idx < 0 or idx >= len(self.registry):
                continue
            item = self.registry[idx]
            if category_filter and item.get("category") not in category_filter:
                continue
            res.append(item)
        return res
