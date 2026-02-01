from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from datetime import datetime

class Evidence(BaseModel):
    """Evidence structure"""
    source: str = Field(..., description="Evidence source URL or name")
    content: str = Field(..., description="Evidence content summary")
    credibility: Literal["high", "medium", "low"] = Field(
        default="medium", description="Source credibility"
    )


class ProcessTrace(BaseModel):
    """Complete workflow trace for Reflector to analyze each stage quality"""
    
    # Planner stage output
    planner_output: dict = Field(
        default_factory=dict,
        description="Planner output: extracted_claims, selected_rules, search_queries"
    )
    
    # Investigator stage output
    investigator_output: dict = Field(
        default_factory=dict,
        description="Investigator output: evidence_items, raw_search_response"
    )
    
    # Judge stage reasoning
    judge_reasoning: str = Field(
        default="",
        description="Judge's detailed reasoning process"
    )


class Verdict(BaseModel):
    """AgentA's verdict output"""
    case_id: str = Field(..., description="Unique case ID")
    claim: str = Field(..., description="Original claim to verify")
    
    # Verdict result (MUST be True or False only)
    verdict: Literal["True", "False"] = Field(
        ..., description="Final verdict: True or False only"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level")
    
    # Explainability log
    reasoning: str = Field(..., description="Reasoning process description")
    evidence: List[Evidence] = Field(default_factory=list, description="Evidence used")
    used_rules: List[str] = Field(
        default_factory=list, description="List of rule IDs used"
    )
    rule_match_quality: Literal["high", "medium", "low", "none"] = Field(
        default="none", description="Rule match quality"
    )
    
    # Workflow trace (for Reflector)
    process_trace: Optional[ProcessTrace] = Field(
        default=None,
        description="Complete workflow trace including Planner/Investigator/Judge stage outputs"
    )
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def to_display(self) -> str:
        """Format output for human viewing"""
        base_display = f"""
[Verdict Result]
Case ID: {self.case_id}
Claim: {self.claim}
Verdict: {self.verdict} (Confidence: {self.confidence:.2f})

[Reasoning Process]
{self.reasoning}

[Evidence Used]
{chr(10).join(f"- [{e.credibility}] {e.source}: {e.content}" for e in self.evidence)}

[Rules Used]
{', '.join(self.used_rules) if self.used_rules else 'No rules matched'}

[Rule Match Quality] {self.rule_match_quality}
        """.strip()
        
        # Add workflow trace summary
        if self.process_trace:
            trace = self.process_trace
            trace_summary = f"""

[Workflow Trace]
- Planner: Extracted {len(trace.planner_output.get('extracted_claims', []))} claims, selected {len(trace.planner_output.get('selected_rules', []))} rules
- Investigator: Collected {len(trace.investigator_output.get('evidence_items', []))} evidence items
- Judge: {trace.judge_reasoning[:100]}{'...' if len(trace.judge_reasoning) > 100 else ''}"""
            base_display += trace_summary
        
        return base_display


class HumanFeedback(BaseModel):
    """Human feedback structure"""
    case_id: str = Field(..., description="Corresponding case ID")
    ground_truth: Literal["True", "False", "Unverifiable"] = Field(
        ..., description="Correct answer"
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
