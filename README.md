# Conversation Evaluation Platform

Production-ready scaffold for scoring conversation turns across many facets.

Features:
- Data cleaning & facet registry generation
- Embeddings + FAISS retrieval
- Pluggable scoring engine (MOCK_MODE for demos)
- FastAPI backend & Streamlit UI
- Docker compose for api + ui

See `scripts/` for data preparation and `streamlit_ui/` for the frontend.

Run (development):

1. Create env: `python -m venv .venv && .venv\\Scripts\\activate`
2. Install: `pip install -r requirements.txt`
3. Prepare data: `python scripts/prepare_data.py`
4. Run API: `uvicorn app.api.main:app --reload --port 8000`
5. Run UI: `streamlit run streamlit_ui/app.py`

Architecture
------------

Conversation
	↓
Embedding (SentenceTransformers)
	↓
FAISS Retrieval
	↓
Facet Selection (registry.json)
	↓
Batch Scoring (local LLM or mock)
	↓
Results (score, confidence, reason, evidence)

Notes
-----
- Embeddings are used for retrieval and scalability; they are NOT used for scoring.
- Scoring is performed by a local open-weight LLM (configurable) or by the mock scorer.
- Confidence is currently self-reported by the model. Future work includes log-prob calibration, ensembles, and calibration techniques.

