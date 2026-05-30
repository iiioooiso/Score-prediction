% Conversation Evaluation Platform — Professional Technical Report

**Deployment Links (first page)**

- Backend API (dev): http://localhost:8000
- Streamlit UI (dev): http://localhost:8501
- Docker Hub image (example): https://hub.docker.com/r/your-org/conversation-eval
- CI/CD (GitHub Actions): https://github.com/your-org/conversation-eval/actions
- Kubernetes manifests: https://github.com/your-org/conversation-eval/deploy/k8s

Replace the example links above with your production URLs. These should be presented on the cover page of any PDF or printed report.

---

# Executive Summary

This report documents the design, implementation, and operational guidance for the Conversation Evaluation Platform — a retrieval-augmented system that evaluates natural-language conversations against a large catalog of human-authored facets and produces evidence-backed 1–5 scores with confidence estimates.

The platform was built to support large-scale, repeatable evaluation workflows for research or production use. It emphasizes:

- Facets-as-data: a single, versioned `facet_registry.json` is the source-of-truth for all evaluative checks.
- Retrieval-first design: embed facet descriptions and use FAISS to retrieve a compact set of candidate facets before scoring.
- Cost-efficient and robust scoring: batch facets per LLM request, robustly parse model output to structured JSON, and provide a deterministic `MOCK_MODE` for testing and demo.

This document is intended for technical stakeholders (engineers, DevOps, security reviewers) and product leads who need a full understanding of the system architecture, APIs, deployment options, internal operations, and runbook guidance.

---

# Table of Contents

1. Executive Summary
2. System Architecture (diagram + components)
3. API Reference (endpoints and examples)
4. Data Pipeline & Facet Registry
5. Scoring Engine & Model Details
6. Operations: deployment, runbook, and scripts
7. Security, Privacy, and Compliance
8. Observability and Monitoring
9. Performance & Scaling
10. Troubleshooting and Common Errors
11. Roadmap and Next Steps
12. Appendix: File Map and Commands

---

# 2. System Architecture

High-level architecture (mermaid):

```mermaid
graph LR
  User[User / Operator] -->|web| UI[Streamlit UI]
  UI -->|HTTP| API[FastAPI Backend]
  API --> Retriever[Retriever Service]
  Retriever -->|top-K| FAISS[FAISS Index]
  FAISS --> Registry[Facet Registry (JSON)]
  API -->|batch prompts| LLM[LLMScorer (transformers)]
  LLM --> Parser[Parser & Validator]
  Parser --> API
  API -->|results| UI
  DataPrep[Data Prep scripts] --> Registry
  DataPrep --> Embeddings[Embedding Model]
  Embeddings --> FAISS
```

Components (detailed):

- Streamlit UI (`streamlit_ui/app.py`): lightweight user-facing interface that posts evaluation requests to the API. It supports per-request `Mock Mode` override and top-K controls.
- FastAPI Backend (`app/api/main.py`): orchestrates retrieval and scoring, exposes endpoints `/evaluate`, `/facets`, `/facets/search`, and `/health`.
- Retriever (`app/services/retriever.py`): normalizes conversation text, computes embeddings (if necessary), and returns top-K facets from FAISS.
- Storage: FAISS index (`data/faiss_index.bin`) and embeddings vector file (e.g., `data/facet_vectors.npy`). These are precomputed by `scripts/generate_faiss.py`.
- Facet Registry (`data/processed/facet_registry.json`): enriched metadata per facet; used to construct human-readable prompts and map IDs to descriptive names.
- Scoring Engine (`app/scoring/scorer.py`): `MockScorer` for deterministic output in demo mode; `LLMScorer` wraps inference, supports batch scoring, lazy model load, and interprets raw model outputs.
- Prompt Builder (`app/scoring/prompt_builder.py`): consistent prompt templates for single and batch scoring.
- Parser (`app/scoring/parser.py`): robust JSON extraction with Pydantic validation to produce structured `score`, `confidence`, `reason`, and `evidence` fields.

---

# 3. API Reference

Base URL (dev): `http://localhost:8000`

Endpoints

- `GET /health`
  - Purpose: health check
  - Returns: `{"status": "ok"}`

- `GET /facets`
  - Purpose: list all facets and metadata
  - Query params: `category`, `inferability`, `limit` (optional)

- `POST /evaluate`
  - Purpose: core scoring endpoint
  - Payload (JSON):

```json
{
  "conversation": "I have been feeling tired and not sleeping well.",
  "top_k": 20,
  "category_filter": ["sleep", "mood"],
  "mode": "retrieval",  // or "all"
  "mock_mode": true
}
```

Response (abridged):

```json
{
  "results": [
    {
      "facet_id": 12,
      "facet_name": "Sleep Problems",
      "score": 4,
      "confidence": 0.87,
      "reason": "User states difficulty sleeping",
      "evidence": ["I can't fall asleep"]
    }
  ],
  "facets_evaluated": 20,
  "inference_time": 1.23,
  "average_confidence": 0.71
}
```

Notes:

- `mode`: `retrieval` — fetch top_k via FAISS and score; `all` — score all facets (use with caution: expensive).
- `mock_mode`: boolean override to force `MockScorer` behavior.
- `top_k`: how many facets to retrieve and score.

Example cURL request:

```bash
curl -X POST http://localhost:8000/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"conversation":"I feel anxious and can't sleep","top_k":10,"mock_mode":true}'
```

API docs: run the backend and visit `/docs` for the interactive OpenAPI UI.

---

# 4. Data Pipeline & Facet Registry

Source data:

- Raw CSV: `Facets Assignment.csv` (raw inputs)

Processing scripts and outputs:

- `scripts/prepare_data.py` — cleans raw CSV, enriches facet descriptions, infers categories/subcategories, and writes `data/processed/processed_facets.csv` and `data/processed/facet_registry.json`.
- `scripts/generate_faiss.py` — uses `sentence-transformers` (configurable via `app/core/config.py`) to produce embeddings and a FAISS index (`data/faiss_index.bin`) and vectors file (`data/facet_vectors.npy`).

Facet registry schema (example):

```json
{
  "facet_id": 12,
  "facet_name": "Sleep Problems",
  "category": "Sleep",
  "description": "User reports difficulty falling or staying asleep.",
  "inferability": "high",
  "evidence_type": "sentence"
}
```

Updating facets:

1. Edit input CSV or the processed CSV.
2. Run `python scripts/prepare_data.py` to refresh `facet_registry.json`.
3. Run `python scripts/generate_faiss.py` to rebuild embeddings and FAISS index.

---

# 5. Scoring Engine & Model Details

Configuration: see `app/core/config.py`. Notable settings:

- `EMBEDDING_MODEL` — SentenceTransformers model used for embeddings, default `all-MiniLM-L6-v2`.
- `SCORING_MODEL` — name of transformers model to use for LLM scoring (e.g., `Qwen2.5-7B-Instruct`).
- `SCORER_BATCH_SIZE` — how many facets to include in a single LLM call.

Behavior:

- `MockScorer`: deterministic hashing-based scoring (fast, cheap, reproducible). Used when `MOCK_MODE=true`.
- `LLMScorer`: lazy-loads tokenizer and model, builds batch prompts using `prompt_builder`, calls `model.generate(...)` (or another inference method), and hands raw text to `parser.parse_and_validate()`.
- Parser extracts JSON responses, maps parsed entries back to facets (by `facet_id` or by order), and returns structured results.

Recommendations for production:

- Use GPU-backed nodes for large models or use managed LLM services to avoid local hardware complexity.
- Consider quantized or distilled models for CPU-only deployments.

---

# 6. Operations: deployment, runbook, and scripts

Local development (quick start):

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
python scripts/prepare_data.py
python scripts/generate_faiss.py
.venv\Scripts\python -m uvicorn app.api.main:app --reload --port 8000
.venv\Scripts\python -m streamlit run streamlit_ui/app.py
```

Docker Compose (example):

```bash
docker-compose build
docker-compose up -d
```

Recommended start/stop order (runbook):

1. Ensure `data/processed/facet_registry.json` and FAISS index are present (run `prepare_data` + `generate_faiss` if needed).
2. Start the backend API (Uvicorn) or the inference service.
3. Start the Streamlit UI or any front-end layers.

Regenerating FAISS (if facets change):

```powershell
python scripts/prepare_data.py
python scripts/generate_faiss.py
# restart API if index path or registry path changed
```

Model updates: to change the `SCORING_MODEL` in production, plan a rolling restart of inference workers and verify prompt parsing on a staging set.

---

# 7. Security, Privacy, and Compliance

- Ensure all production endpoints use TLS. Terminate TLS at load balancer or ingress.
- Protect `/evaluate` with authentication and role-based access in production.
- Conversations may contain PII or PHI — adopt retention policies and encryption at rest.
- If using third-party LLM APIs, verify data usage terms and user consent requirements.

---

# 8. Observability and Monitoring

Instrument the following metrics:

- `requests_total`, `requests_failed`
- `inference_time_seconds` (per call)
- `parse_errors_total`
- `average_confidence`
- `faiss_query_time_seconds`

Logs should contain:

- request id, timestamp, top-k facet ids returned, prompt size (tokens or characters), model generation duration, parse results (or parse error), and truncated conversation for troubleshooting.

Export to Prometheus + Grafana for dashboards and alerts.

---

# 9. Performance & Scaling

- Tuning knobs:
  - `SCORER_BATCH_SIZE`: larger batches reduce model calls but increase prompt length and parsing complexity.
  - `N_RETRIEVAL_K`: increasing top-K raises recall but increases inference workload.
  - FAISS index type: HNSW is a good tradeoff for recall and speed; consider IVF/PQ for very large datasets.
- Production suggestions:
  - Use a separate inference service for the model: dedicate GPU instance(s) and serve requests over gRPC/HTTP.
  - Cache embeddings and recent evaluation results.

---

# 10. Troubleshooting and Common Errors

1. `ModuleNotFoundError: No module named 'app.core'; 'app' is not a package` when running `streamlit run streamlit_ui/app.py`.
   - Root cause: Streamlit may import the script under a top-level module name that conflicts with the `app` package.
   - Fixes:
     - Run Streamlit from the project root: `.venv\Scripts\python -m streamlit run streamlit_ui/app.py`
     - Ensure the project root is on `PYTHONPATH`: `set PYTHONPATH=D:\Ai-ml-Assign` (Windows) or `export PYTHONPATH=/path/to/repo`
     - The repo already includes a dynamic loader in `streamlit_ui/app.py` to import `app/core/config.py` by path as a fallback.

2. `pydantic.errors.PydanticImportError: BaseSettings has been moved`.
   - Fix: install `pydantic-settings` or migrate to the new settings package; update `requirements.txt` accordingly.

3. SyntaxError / IndentationError in `app/scoring/scorer.py`.
   - Fix: run `python -m py_compile app/scoring/scorer.py` and inspect traceback; ensure try/except blocks are balanced.

4. Model OOM (out-of-memory) during `LLMScorer._load()` or `model.generate()`.
   - Fix: switch to a smaller model, use model quantization, or move to GPU with larger VRAM. Consider vLLM or remote LLM provider.

---

# 11. Roadmap and Next Steps

- Productionize inference: separate inference service, autoscaling, GPU provisioning.
- Integrate a managed vector DB for higher throughput and persistence (Weaviate, Milvus, Pinecone).
- Add a comprehensive `pytest` suite and CI pipelines for unit and integration tests.
- Add a web-based admin interface for facet editing and versioned registry management.

---

# 12. Appendix: File Map and Commands

Key files and directories:

- `app/` — backend application code
  - `app/api/main.py` — API routes
  - `app/core/config.py` — runtime configuration
  - `app/scoring/` — scorer, prompt builder, parser
  - `app/retrieval/` — embedding helpers and FAISS utilities
  - `app/services/retriever.py` — retrieval orchestration
- `streamlit_ui/app.py` — UI frontend
- `scripts/prepare_data.py` — data cleaning and facet registry generation
- `scripts/generate_faiss.py` — embedding and FAISS index creation
- `data/` — raw & processed data, vectors, and index files
- `requirements.txt`, `Dockerfile`, `docker-compose.yml`

Useful commands summary:

```powershell
# Setup
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

# Prepare data and FAISS
python scripts/prepare_data.py
python scripts/generate_faiss.py

# Run backend
.venv\Scripts\python -m uvicorn app.api.main:app --reload --port 8000

# Run Streamlit UI
.venv\Scripts\python -m streamlit run streamlit_ui/app.py

# Compile code quickly for syntax errors
python -m py_compile app/scoring/scorer.py
```

---

If you want, I will:

- export `REPORT.md` to a print-ready PDF and ensure mermaid diagrams render cleanly, or
- generate a short slide deck summarizing the architecture and operational playbook.

Tell me which output you prefer (PDF or slides) and whether to include hosted deployment screenshots or live endpoints; I'll produce the export next.
