import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so `from app.*` imports work
# when Streamlit runs with `streamlit run streamlit_ui/app.py`.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import requests
import importlib.util

# Load project settings from `app/core/config.py` by file path to avoid
# a name collision when Streamlit loads this script as a module named
# `app` (which would shadow the package directory). This ensures we
# get the real `settings` object defined in the project's config.
_config_path = Path(_ROOT) / "app" / "core" / "config.py"
settings = None
if _config_path.exists():
    spec = importlib.util.spec_from_file_location("project_config", str(_config_path))
    project_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(project_config)  # type: ignore
    settings = getattr(project_config, "settings", None)
else:
    # fallback to attempting a normal import (best-effort)
    try:
        from app.core.config import settings as _s  # type: ignore
        settings = _s
    except Exception:
        settings = None

# Minimal fallback when config can't be loaded
if settings is None:
    class _FallbackSettings:
        MOCK_MODE = True

    settings = _FallbackSettings()

API_URL = os.getenv("API_URL", "http://localhost:8000")


def call_api(conversation: str, top_k: int, categories: list, mode: str = "retrieval", mock_mode: bool | None = None):
    payload = {
        "conversation": conversation,
        "top_k": top_k,
        "category_filter": categories or None,
        "mode": mode,
    }
    if mock_mode is not None:
        payload["mock_mode"] = mock_mode
    resp = requests.post(f"{API_URL}/evaluate", json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def main():
    st.set_page_config(page_title="Conversation Evaluation", layout="wide")
    st.title("Conversation Evaluation Platform")

    with st.form("eval_form"):
        conversation = st.text_area("Conversation input", height=200)
        mode = st.radio("Evaluation Mode", options=["retrieval", "all"], index=0, horizontal=True)
        top_k = st.slider("Top K facets", min_value=5, max_value=200, value=20)
        categories = st.text_input("Category filter (comma-separated)")
        mock_mode_override = st.checkbox("Mock Mode (override server)", value=settings.MOCK_MODE)
        submitted = st.form_submit_button("Evaluate")

    if submitted and conversation.strip():
        categories_list = [c.strip() for c in categories.split(",") if c.strip()]
        try:
            result = call_api(conversation, top_k, categories_list, mode=mode, mock_mode=mock_mode_override)
        except Exception as e:
            st.error(f"API call failed: {e}")
            return

        rows = result.get("results", [])
        facets_evaluated = result.get("facets_evaluated", len(rows))
        inference_time = result.get("inference_time", 0.0)
        avg_conf = result.get("average_confidence", 0.0)

        st.subheader("Metrics")
        cols = st.columns(3)
        cols[0].metric("Facets Evaluated", facets_evaluated)
        cols[1].metric("Inference Time (s)", f"{inference_time:.2f}")
        cols[2].metric("Average Confidence", f"{avg_conf:.2f}")

        st.subheader("Results")
        if rows:
            # prepare table rows
            table = []
            for r in rows:
                evidence = r.get("evidence")
                ev_text = ", ".join(evidence) if evidence else ""
                table.append({
                    "facet_id": r.get("facet_id"),
                    "facet_name": r.get("facet_name"),
                    "score": r.get("score"),
                    "confidence": r.get("confidence"),
                    "reason": r.get("reason"),
                    "evidence": ev_text,
                })
            st.dataframe(table)
        else:
            st.write("No results returned")


if __name__ == "__main__":
    main()
