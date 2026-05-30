from __future__ import annotations
import hashlib
from typing import Dict, Any, List
from app.core import config
from app.scoring.prompt_builder import build_prompt, build_batch_prompt
from app.scoring.parser import parse_and_validate
from app.core.config import settings


class BaseScorer:
    def score(self, conversation: str, facet: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()


class MockScorer(BaseScorer):
    def score(self, conversation: str, facet: Dict[str, Any]) -> Dict[str, Any]:
        h = int(hashlib.sha256((conversation + facet.get("facet_name", "")).encode()).hexdigest(), 16)
        score = (h % 5) + 1
        confidence = 0.2 + ((h % 80) / 100)
        reason = f"Mock: deterministic signal for {facet.get('facet_name')}"
        # simple evidence extraction: return sentences that contain words from facet name
        conv = (conversation or "").lower()
        evidence = []
        if conv and facet.get("facet_name"):
            words = [w for w in facet.get("facet_name", "").lower().split() if len(w) > 3]
            sentences = [s.strip() for s in conversation.split(".") if s.strip()]
            for w in words:
                for s in sentences:
                    if w in s.lower() and s not in evidence:
                        evidence.append(s)
        return {"score": int(score), "confidence": round(float(confidence), 3), "reason": reason, "evidence": evidence}

    def score_batch(self, conversation: str, facets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not facets:
            return []
        # chunk facets to avoid hitting model context/window limits
        chunk_size = getattr(settings, "SCORER_BATCH_SIZE", 20)
        results: List[Dict[str, Any]] = []

        # load model once
        try:
            self._load()
        except Exception as e:
            return [
                {"facet_id": f.get("facet_id"), "facet_name": f.get("facet_name"), "score": 3, "confidence": 0.05, "reason": f"fallback: model load error: {e}", "evidence": []}
                for f in facets
            ]

        for i in range(0, len(facets), chunk_size):
            chunk = facets[i : i + chunk_size]
            prompt = build_batch_prompt(conversation, chunk)
            try:
                inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True)
                # move inputs to model device if possible
                try:
                    device = next(self._model.parameters()).device
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                except Exception:
                    pass
                # choose max tokens based on number of facets
                max_new = min(2048, max(128, len(chunk) * 64))
                gen = self._model.generate(**inputs, max_new_tokens=max_new, do_sample=False)
                # extract generation after prompt
                input_len = inputs["input_ids"].shape[1]
                gen_ids = gen[0][input_len:]
                out = self._tokenizer.decode(gen_ids, skip_special_tokens=True).strip()
                parsed = parse_and_validate(out, expect_batch=True)
                # parsed is a list of score dicts; align with chunk facets
                # if parsed entries include facet_id, map by id; otherwise map by order
                if isinstance(parsed, list) and all((isinstance(p.get("facet_id"), int) for p in parsed)):
                    for f in chunk:
                        fid = f.get("facet_id")
                        match = next((p for p in parsed if p.get("facet_id") == fid), None)
                        if match:
                            results.append({
                                "facet_id": fid,
                                "facet_name": f.get("facet_name"),
                                "score": int(match.get("score")),
                                "confidence": float(match.get("confidence")),
                                "reason": match.get("reason", "").strip(),
                                "evidence": match.get("evidence"),
                            })
                        else:
                            results.append({"facet_id": fid, "facet_name": f.get("facet_name"), "score": 3, "confidence": 0.05, "reason": "fallback: missing parsed item", "evidence": []})
                else:
                    # assume same order
                    for idx, f in enumerate(chunk):
                        p = parsed[idx] if idx < len(parsed) else None
                        if p:
                            results.append({
                                "facet_id": f.get("facet_id"),
                                "facet_name": f.get("facet_name"),
                                "score": int(p.get("score")),
                                "confidence": float(p.get("confidence")),
                                "reason": p.get("reason", "").strip(),
                                "evidence": p.get("evidence"),
                            })
                        else:
                            results.append({"facet_id": f.get("facet_id"), "facet_name": f.get("facet_name"), "score": 3, "confidence": 0.05, "reason": "fallback: missing parsed item", "evidence": []})
            except Exception as e:
                # append fallback entries for this chunk and continue
                for f in chunk:
                    results.append({"facet_id": f.get("facet_id"), "facet_name": f.get("facet_name"), "score": 3, "confidence": 0.05, "reason": f"fallback: generation/parse error: {e}", "evidence": []})
                continue

        return results


def get_scorer(mock_mode: bool = True) -> BaseScorer:
    if mock_mode:
        return MockScorer()
    return LLMScorer()

