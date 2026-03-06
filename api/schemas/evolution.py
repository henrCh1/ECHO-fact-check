"""Schemas for human-in-the-loop evolution workflow."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class EvolutionMetaResponse(BaseModel):
    """Evolution status returned alongside verify responses."""

    pending_count: int = 0
    review_batch_ready: bool = False
    review_batch_id: Optional[str] = None


class PendingReviewEvidence(BaseModel):
    source: str
    content: str
    credibility: Literal["high", "medium", "low"]


class PendingReviewProcessTrace(BaseModel):
    planner_output: dict = Field(default_factory=dict)
    investigator_output: dict = Field(default_factory=dict)
    judge_reasoning: str = ""


class PendingReviewCaseResponse(BaseModel):
    case_id: str
    claim: str
    verdict: Literal["True", "False"]
    confidence: float
    reasoning: str
    evidence: List[PendingReviewEvidence] = Field(default_factory=list)
    used_rules: List[str] = Field(default_factory=list)
    rule_match_quality: Literal["high", "medium", "low", "none"] = "none"
    process_trace: Optional[PendingReviewProcessTrace] = None
    timestamp: datetime
    mode: Literal["evolving"] = "evolving"


class ReviewBatchResponse(BaseModel):
    batch_id: str
    status: Literal["pending_review", "processing", "completed"]
    created_at: datetime
    updated_at: datetime
    deferred_count: int = 0
    cases: List[PendingReviewCaseResponse] = Field(default_factory=list)


class PendingReviewResponse(BaseModel):
    has_pending_batch: bool
    pending_count: int = 0
    batch: Optional[ReviewBatchResponse] = None


class ReviewFeedbackItemRequest(BaseModel):
    case_id: str
    judgment_correct: bool
    reasoning_correct: bool
    comment: Optional[str] = None


class ReviewBatchSubmitRequest(BaseModel):
    feedback: List[ReviewFeedbackItemRequest] = Field(
        ..., min_length=1, description="Feedback items for all cases in the batch"
    )


class ReviewBatchSubmitResponse(BaseModel):
    batch_id: str
    status: Literal["completed"]
    processed_cases: int
    updates_applied: int = 0
    trial_rules_generated: int = 0
    detection_rules_generated: int = 0
    trust_rules_generated: int = 0
    next_batch_ready: bool = False
    next_batch_id: Optional[str] = None
