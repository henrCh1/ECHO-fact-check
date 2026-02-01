"""Verification Schemas"""
from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from datetime import datetime


class EvidenceResponse(BaseModel):
    """Evidence in response"""
    source: str
    content: str
    credibility: Literal["high", "medium", "low"]


class ProcessTraceResponse(BaseModel):
    """Process trace in response"""
    planner_output: dict = Field(default_factory=dict)
    investigator_output: dict = Field(default_factory=dict)
    judge_reasoning: str = ""


class VerifyRequest(BaseModel):
    """Single claim verification request"""
    claim: str = Field(..., description="The claim text to verify")
    mode: Literal["static", "evolving"] = Field(
        default="static",
        description="Verification mode: 'static' uses existing rules only, 'evolving' triggers rule evolution"
    )


class VerifyResponse(BaseModel):
    """Verification result response"""
    case_id: str
    claim: str
    verdict: Literal["True", "False"]
    confidence: float
    reasoning: str
    evidence: List[EvidenceResponse]
    used_rules: List[str]
    rule_match_quality: Literal["high", "medium", "low", "none"]
    process_trace: Optional[ProcessTraceResponse] = None
    timestamp: datetime
    mode: str = "static"
    
    class Config:
        from_attributes = True


class BatchVerifyRequest(BaseModel):
    """Batch verification request (CSV upload handled separately)"""
    mode: Literal["static", "evolving"] = Field(
        default="static",
        description="Verification mode for all claims"
    )


class BatchTaskResponse(BaseModel):
    """Batch task status response"""
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    total: int
    completed: int
    failed: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None


class BatchResultItem(BaseModel):
    """Single item in batch result"""
    row_number: int
    claim: str
    verdict: Optional[Literal["True", "False"]] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    status: Literal["success", "failed"] = "success"
    error: Optional[str] = None
