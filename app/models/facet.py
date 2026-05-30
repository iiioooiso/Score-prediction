from pydantic import BaseModel
from typing import Optional


class Facet(BaseModel):
    facet_id: int
    facet_name: str
    category: str
    subcategory: Optional[str] = None
    description: Optional[str] = None
    inferability: str = "medium"
    evidence_type: str = "behavioral"
