from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Rule(BaseModel):
    """Single rule data structure"""
    rule_id: str = Field(..., description="Unique rule ID, e.g., shr-00001")
    type: Literal["strategy", "tool_template", "pitfall"] = Field(
        ..., description="Rule type: strategy/tool_template/pitfall"
    )
    condition: str = Field(..., description="Trigger condition, e.g., 'IF source_type=social_media'")
    action: str = Field(..., description="Execution action, e.g., 'Requires cross-validation'")
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Rule confidence"
    )
    evidence_count: int = Field(default=1, description="Number of cases supporting this rule")
    created_from: Optional[str] = Field(None, description="Source case ID")
    created_at: datetime = Field(default_factory=datetime.now)
    parent_rule: Optional[str] = Field(None, description="Parent rule ID (used when refining)")
    description: str = Field(..., description="Rule description")
    active: bool = Field(default=True, description="Whether active")
    memory_type: Optional[Literal["detection", "trust"]] = Field(
        None, 
        description="Memory type: detection (for false info) or trust (for true info)"
    )
    
    @field_validator('evidence_count', mode='before')
    @classmethod
    def fix_evidence_count(cls, v: Any) -> int:
        """Auto-fix evidence_count type errors"""
        if isinstance(v, str):
            # Detect common error patterns
            if 'original value + 1' in v.lower() or '+' in v:
                logger.warning(f"⚠️ Detected invalid evidence_count format: '{v}', auto-fixing to 1")
                return 1
            # Try to parse as integer
            try:
                return int(v)
            except ValueError:
                logger.error(f"❌ Cannot parse evidence_count: '{v}', using default value 1")
                return 1
        return int(v)
    
    @field_validator('type', mode='before')
    @classmethod
    def validate_type(cls, v: Any) -> str:
        """Validate and auto-fix type field"""
        valid_types = {"strategy", "tool_template", "pitfall"}
        if v not in valid_types:
            logger.warning(f"⚠️ Invalid rule type: '{v}', auto-fixing to 'strategy'")
            return "strategy"
        return v
    
    @field_validator('confidence', mode='before')
    @classmethod
    def validate_confidence(cls, v: Any) -> float:
        """Validate and clamp confidence to [0.0, 1.0]"""
        try:
            conf = float(v)
            if conf < 0.0:
                logger.warning(f"⚠️ Confidence {conf} < 0.0, clamping to 0.0")
                return 0.0
            if conf > 1.0:
                logger.warning(f"⚠️ Confidence {conf} > 1.0, clamping to 1.0")
                return 1.0
            return conf
        except (ValueError, TypeError):
            logger.error(f"❌ Cannot parse confidence: '{v}', using default 0.5")
            return 0.5


class Playbook(BaseModel):
    """Playbook data structure"""
    version: str = Field(..., description="Version number, e.g., v1.0")
    rules: List[Rule] = Field(default_factory=list, description="Rule list")
    last_updated: datetime = Field(default_factory=datetime.now)
    total_cases_processed: int = Field(default=0, description="Total cases processed")
    
    def get_active_rules(self) -> List[Rule]:
        """Get all active rules"""
        return [r for r in self.rules if r.active]
    
    def add_rule(self, rule: Rule) -> None:
        """Add new rule"""
        self.rules.append(rule)
        self.last_updated = datetime.now()
    
    def update_rule_confidence(self, rule_id: str, new_confidence: float) -> None:
        """Update rule confidence"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                rule.confidence = new_confidence
                rule.evidence_count += 1
                break
        self.last_updated = datetime.now()


class DeltaUpdate(BaseModel):
    """Curator output delta update"""
    action: Literal["add_rule", "update_rule", "deprecate_rule", "refine_rule", "no_action"]
    target_rule_id: Optional[str] = None  # Required for update/deprecate
    new_rule: Optional[Rule] = None       # Required for add/refine
    update_fields: Optional[dict] = None  # Fields to modify for update
    reason: str = Field(..., description="Update reason")
    target_memory: Optional[Literal["detection", "trust"]] = Field(
        default="detection",
        description="Target memory: detection (for false info rules) or trust (for true info rules)"
    )

