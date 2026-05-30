import json
from typing import Any, Dict
from pydantic import BaseModel, ValidationError, conint, confloat, constr
from typing import List, Optional


class ScoreOutput(BaseModel):
    facet_id: Optional[int] = None
    score: conint(ge=1, le=5)
    confidence: confloat(ge=0.0, le=1.0)
    reason: constr(min_length=1, max_length=1000)
    evidence: Optional[List[constr(min_length=1, max_length=500)]] = None


def _extract_json(text: str):
    """Attempt to extract the first JSON value (object or array) from text.

    This attempts incremental `json.loads` on substrings starting at the first
    occurrence of '{' or '[' until a valid JSON value is parsed.
    """
    s = text
    idx_obj = s.find("{")
    idx_arr = s.find("[")
    starts = [i for i in (idx_obj, idx_arr) if i != -1]
    if not starts:
        raise ValueError("No JSON object or array found in text")
    start = min(starts)
    # try incremental decoding
    for j in range(start + 1, min(len(s), start + 10000) + 1):
        candidate = s[start:j]
        try:
            return json.loads(candidate)
        except Exception:
            continue
    raise ValueError("Could not extract a valid JSON value from model output")


def parse_and_validate(text: str, expect_batch: bool = False) -> Any:
    obj = _extract_json(text)
    if expect_batch:
        if not isinstance(obj, list):
            raise ValueError("Expected a JSON array for batch output")
        out = []
        for item in obj:
            parsed = ScoreOutput.parse_obj(item)
            out.append(parsed.dict())
        return out
    # single
    if isinstance(obj, list):
        # accept single-element array
        if len(obj) == 1:
            parsed = ScoreOutput.parse_obj(obj[0])
            return parsed.dict()
        raise ValueError("Expected a single JSON object but found an array")
    parsed = ScoreOutput.parse_obj(obj)
    return parsed.dict()
