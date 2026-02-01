"""HumanFeedback Schema - 2-class version"""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


class HumanFeedback(BaseModel):
    """Human feedback structure - 2-class version (True/False)"""
    case_id: str = Field(..., description="Corresponding case ID")
    ground_truth: Literal["True", "False"] = Field(
        ..., description="Correct answer (2-class: True or False)"
    )
    feedback_type: Literal[
        "correct_verdict_correct_reasoning",
        "correct_verdict_wrong_reasoning", 
        "wrong_verdict_correct_reasoning",
        "wrong_verdict_wrong_reasoning"
    ] = Field(..., description="Feedback type")
    specific_issue: Optional[str] = Field(
        None, description="Specific issue description, e.g., 'Rule shr-00001 not applicable in this context'"
    )
    suggested_fix: Optional[str] = Field(
        None, description="Improvement suggestion, e.g., 'Need to add source classification'"
    )
    timestamp: datetime = Field(default_factory=datetime.now)
