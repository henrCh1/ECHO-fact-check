"""Playbook Schemas"""
from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from datetime import datetime


class RuleResponse(BaseModel):
    """Rule response model"""
    rule_id: str
    type: Literal["strategy", "tool_template", "pitfall"]
    condition: str
    action: str
    description: str
    confidence: float
    evidence_count: int
    memory_type: Optional[Literal["detection", "trust"]] = None
    active: bool = True
    created_from: Optional[str] = None
    created_at: Optional[datetime] = None
    parent_rule: Optional[str] = None
    
    class Config:
        from_attributes = True


class PlaybookStatusResponse(BaseModel):
    """Playbook status response"""
    version: str
    detection_rules_count: int
    trust_rules_count: int
    total_active_rules: int
    total_cases_processed: int
    last_updated: datetime


class RuleListResponse(BaseModel):
    """List of rules response"""
    detection_rules: List[RuleResponse]
    trust_rules: List[RuleResponse]
    total_count: int


class PlaybookSwitchRequest(BaseModel):
    """Request to switch playbook"""
    playbook_name: Literal["default", "warmup", "custom"] = Field(
        ..., description="Name of the playbook to switch to"
    )
    custom_path: Optional[str] = Field(
        None, description="Custom path for 'custom' playbook type"
    )
