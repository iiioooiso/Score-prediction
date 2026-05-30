from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    MOCK_MODE: bool = True
    FACETS_CSV_PATH: str = str(Path("data") / "raw" / "Facets Assignment.csv")
    PROCESSED_CSV_PATH: str = str(Path("data") / "processed" / "processed_facets.csv")
    FACET_REGISTRY_PATH: str = str(Path("data") / "processed" / "facet_registry.json")
    FAISS_INDEX_PATH: str = str(Path("data") / "faiss_index.bin")
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    SCORING_MODEL: str = "Qwen2.5-7B-Instruct"
    N_RETRIEVAL_K: int = 20
    SCORER_BATCH_SIZE: int = 20

    class Config:
        env_file = ".env"


settings = Settings()
