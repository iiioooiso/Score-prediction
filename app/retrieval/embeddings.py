from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


def load_embedding_model(name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    return SentenceTransformer(name)


def embed_texts(model: SentenceTransformer, texts: List[str]) -> np.ndarray:
    return model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
