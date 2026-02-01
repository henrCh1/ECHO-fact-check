"""Warmup Schemas"""
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


class WarmupStartRequest(BaseModel):
    """Request to start warmup process"""
    dataset_path: Optional[str] = Field(
        None, 
        description="Path to custom warmup CSV file. If None, uses default data/warmup.csv"
    )
    output_playbook_name: str = Field(
        default="custom",
        description="Name for the generated playbook directory"
    )
    

class WarmupTaskResponse(BaseModel):
    """Warmup task status response"""
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    total_cases: int
    processed_cases: int
    correct_verdicts: int = 0
    incorrect_verdicts: int = 0
    rules_generated: int = 0
    detection_rules: int = 0
    trust_rules: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None
    output_playbook_path: Optional[str] = None


class WarmupDatasetInfo(BaseModel):
    """Information about uploaded warmup dataset"""
    filename: str
    total_rows: int
    columns: list
    sample_claims: list
