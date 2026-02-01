"""History Schemas"""
from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from datetime import datetime


class HistoryItemSummary(BaseModel):
    """Summary of a history item for list view"""
    case_id: str
    claim_summary: str = Field(..., description="Truncated claim text")
    verdict: Literal["True", "False"]
    confidence: float
    rule_match_quality: Literal["high", "medium", "low", "none"]
    timestamp: datetime
    mode: str = "static"


class HistoryListResponse(BaseModel):
    """Paginated history list response"""
    items: List[HistoryItemSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class HistoryFilterParams(BaseModel):
    """Filter parameters for history query"""
    verdict: Optional[Literal["True", "False"]] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    mode: Optional[Literal["static", "evolving"]] = None
    search: Optional[str] = None
