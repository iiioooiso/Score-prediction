# Conversation Evaluation Platform

> A retrieval-augmented evaluation system that scores conversation turns across hundreds of facets, producing evidence-backed 1–5 ratings and confidence scores. Built with FastAPI (backend), Streamlit (UI), FAISS (retrieval), SentenceTransformers (embeddings), and a local LLM scoring component (transformers / torch). Designed for batch scoring, deterministic mock mode, and `facet_registry.json` driven facets-as-data.

---

## Quick Links

- Architecture & diagrams: [ARCHITECTURE.md](ARCHITECTURE.md)
- Streamlit UI: `streamlit_ui/app.py`
- FastAPI backend: `app/api/main.py`
- Facet registry: `data/processed/facet_registry.json`

---

## Highlights

- Central design principle: treat facets as DATA (single source-of-truth file) not code.
- Retrieval + LLM scoring: embed facet text, retrieve top-K candidates with FAISS, batch-score with an LLM (or deterministic Mock mode).
- Batch scoring and parsing: prompts are built for batches to reduce inference calls; parser extracts JSON with `score`, `confidence`, `reason`, and `evidence`.
- Demo-friendly: `MOCK_MODE=true` for deterministic, low-cost runs.

---

## Requirements

- Python 3.11+
- Recommended: GPU + CUDA if using large local LLMs (optional)
- See `requirements.txt` for Python packages (FastAPI, streamlit, sentence-transformers, faiss-cpu, transformers, torch, pydantic-settings, pytest)

---

## Getting started (Windows)

1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -U pip
.venv\Scripts\python -m pip install -r requirements.txt
```

2. Prepare data (creates `data/processed` and `facet_registry.json`):

```powershell
python scripts/prepare_data.py
```

3. Generate embeddings + FAISS index:

```powershell
python scripts/generate_faiss.py
```

4. Start the backend API (local dev):

```powershell
.venv\Scripts\python -m uvicorn app.api.main:app --reload --port 8000
```

5. Start the Streamlit UI (opens at http://localhost:8501):

```powershell
.venv\Scripts\python -m streamlit run streamlit_ui/app.py
```

Notes:
- The UI looks for `API_URL` environment variable (defaults to `http://localhost:8000`).
- You can override/mock at runtime using the `Mock Mode` checkbox in the UI.

---

## Configuration

Core runtime settings live in `app/core/config.py` (pydantic BaseSettings). Key values:

- `MOCK_MODE` — default demo mode when true
- `FACET_REGISTRY_PATH` — path to enriched `facet_registry.json`
- `FAISS_INDEX_PATH` — path to stored FAISS index
- `EMBEDDING_MODEL` — sentence-transformers model used for embeddings
- `SCORING_MODEL` — transformers model name for LLM scoring (local)
- `N_RETRIEVAL_K` — default retrieval K
- `SCORER_BATCH_SIZE` — facets per LLM request

You can set environment variables or a `.env` file at the repo root. Example `.env`:

```
MOCK_MODE=true
API_URL=http://localhost:8000
```

---

## API (summary)

- `GET /health` — simple health check
- `GET /facets` — list available facets and metadata
- `POST /evaluate` — core scoring endpoint. Payload (example):

```json
{
  "conversation": "I have been feeling tired and not sleeping well.",
  "top_k": 20,
  "category_filter": ["sleep", "mood"],
  "mode": "retrieval",
  "mock_mode": true
}
```

Response includes `results` (list of facet scores with `score`, `confidence`, `reason`, and `evidence`), plus metrics (`facets_evaluated`, `inference_time`, `average_confidence`).

Swagger/OpenAPI is available at `/docs` when the server is running.

---

## Developer notes — core files

- `app/api/main.py` — FastAPI app and routes
- `app/scoring/scorer.py` — `MockScorer` and `LLMScorer` (batching, lazy model load)
- `app/scoring/prompt_builder.py` — prompt templates for single/batch scoring
- `app/scoring/parser.py` — robust JSON extraction + pydantic validation
- `app/retrieval/faiss_index.py` — FAISS load/save and search helpers
- `scripts/prepare_data.py` — data cleaning and facet_registry generation
- `scripts/generate_faiss.py` — embeddings and FAISS index creation
- `streamlit_ui/app.py` — web UI

---

## Testing

Run the test suite (if present):

```powershell
.venv\Scripts\python -m pytest -q
```

Add unit tests for new features and CI pipelines as needed.

---

## Docker / Deploy

There is a `Dockerfile` and `docker-compose.yml` scaffold in the repo. Typical flow:

```powershell
docker-compose build
docker-compose up --detach
```

Production recommendations are covered in [ARCHITECTURE.md](ARCHITECTURE.md) (GPU nodes for LLMs, vLLM alternatives, vector DB options).

---

## Contributing

Contributions welcome. Please open issues for bugs or feature requests and submit PRs following the repository style.

---

## Deployment links (replace with your actual links)
- Streamlit UI (Streamlit Cloud / Vercel): [https://streamlit.io/your-deploy](https://score-pred.streamlit.app/)


Replace the URLs above with real deployment URLs for your project.

---

## License & Attribution

Specify your license here (e.g. MIT). Also list any third-party models / datasets used and attribution as necessary.

---

If you'd like, I can also produce a short handout or a printable PDF summary from `ARCHITECTURE.md`.
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

