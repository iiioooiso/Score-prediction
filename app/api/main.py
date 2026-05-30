from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import schemas
from app.services.retriever import Retriever
from app.scoring.scorer import get_scorer
from typing import List
import time

app = FastAPI(title="Conversation Evaluation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    # initialize services
    app.state.retriever = Retriever()
    app.state.scorer = get_scorer(settings.MOCK_MODE)


@app.get("/health")
def health():
    return {"status": "ok", "mock_mode": settings.MOCK_MODE}


@app.get("/facets")
def list_facets(limit: int = 100) -> List[dict]:
    reg = app.state.retriever.registry if hasattr(app.state, "retriever") else []
    return reg[:limit]


@app.get("/facets/search")
def search_facets(q: str, top_k: int = 20):
    reg = app.state.retriever.registry if hasattr(app.state, "retriever") else []
    if not q:
        raise HTTPException(status_code=400, detail="q parameter required")
    # simple substring search over facet_name and description
    ql = q.lower()
    out = [f for f in reg if ql in f.get("facet_name","").lower() or ql in (f.get("description") or "").lower()]
    return out[:top_k]


@app.post("/evaluate", response_model=schemas.EvaluateResponse)
def evaluate(req: schemas.EvaluateRequest):
    retriever: Retriever = app.state.retriever
    # allow per-request mock override
    scorer = get_scorer(req.mock_mode) if req.mock_mode is not None else app.state.scorer

    # determine facets based on mode
    if req.mode == "all":
        reg = retriever.registry if hasattr(retriever, "registry") else []
        facets = [f for f in reg if (not req.category_filter) or (f.get("category") in req.category_filter)]
    else:
        facets = retriever.retrieve(req.conversation, top_k=req.top_k, category_filter=req.category_filter)

    start = time.perf_counter()
    # use batch scoring when available
    if hasattr(scorer, "score_batch"):
        scored = scorer.score_batch(req.conversation, facets)
    else:
        scored = []
        for f in facets:
            s = scorer.score(req.conversation, f)
            scored.append({
                "facet_id": f.get("facet_id"),
                "facet_name": f.get("facet_name"),
                "score": int(s.get("score")),
                "confidence": float(s.get("confidence")),
                "reason": s.get("reason"),
                "evidence": s.get("evidence") if s.get("evidence") else None,
            })
    end = time.perf_counter()
    inference_time = end - start
    facets_evaluated = len(scored)
    avg_conf = float(sum((r.get("confidence") or 0.0) for r in scored) / max(1, facets_evaluated))

    return {"results": scored, "facets_evaluated": facets_evaluated, "inference_time": inference_time, "average_confidence": avg_conf}
