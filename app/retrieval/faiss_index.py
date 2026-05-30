import os
from typing import Tuple
import numpy as np


def save_index(index, path: str):
    import faiss

    faiss.write_index(index, path)


def load_index(path: str):
    import faiss

    if not os.path.exists(path):
        raise FileNotFoundError(f"FAISS index not found: {path}")
    return faiss.read_index(path)


def search_index(index, query_vec: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
    import faiss

    # query_vec should be shape (1, d)
    import numpy as np

    if query_vec.ndim == 1:
        query_vec = query_vec.reshape(1, -1)
    faiss.normalize_L2(query_vec)
    D, I = index.search(query_vec, top_k)
    return D, I
