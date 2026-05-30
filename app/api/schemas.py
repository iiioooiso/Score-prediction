from pydantic import BaseModel, Field
from typing import List, Optional




class EvaluateRequest(BaseModel):
    conversation: str = Field(..., description="Conversation text to evaluate")
    top_k: int = Field(20, description="Number of facets to retrieve and score")
    category_filter: Optional[List[str]] = None
    mode: Optional[str] = Field("retrieval", description="Evaluation mode: 'retrieval' or 'all'")
    mock_mode: Optional[bool] = Field(None, description="Override server MOCK_MODE for this request if set")


class FacetScore(BaseModel):
    facet_id: int
    facet_name: str
    score: int
    confidence: float
    reason: str
    evidence: Optional[List[str]] = None


class EvaluateResponse(BaseModel):
    results: List[FacetScore]
    facets_evaluated: int
    inference_time: float
    average_confidence: float
