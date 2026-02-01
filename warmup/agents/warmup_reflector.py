"""WarmupReflectorAgent: Supervised Reflector"""

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import Literal, Optional
import json

from schemas.verdict import Verdict
from warmup.schemas.feedback import HumanFeedback
from warmup.prompts.warmup_reflector_prompt import WARMUP_REFLECTOR_PROMPT
from config.settings import Settings


class WarmupKeyInsight(BaseModel):
    """Key insight from reflector - Supervised version (with suggested_rule_intent)"""
    error_type: Optional[Literal["false_positive", "false_negative", "insufficient_reasoning", "insufficient_evidence", "missing_rule", "no_obvious_error"]] = None
    
    # Key field: Suggested rule type (based on groundtruth classification)
    suggested_rule_intent: Optional[Literal["detection", "trust"]] = Field(
        default="detection",
        description="Suggested rule intent: detection (identify false info) or trust (identify true info). Can be None if no rule generation needed"
    )
    
    root_cause: str = Field(..., description="Root cause analysis")
    lesson: str = Field(..., description="Extracted lesson learned")
    suggested_action: str = Field(
        ..., 
        description="Suggested improvement action, e.g., 'Add rule', 'Modify rule X', 'Refine rule Y'"
    )
    confidence_impact: float = Field(
        default=0.0,
        description="Impact on related rule confidence (-1.0 to 1.0)"
    )


class WarmupReflectorAgent:
    """Supervised Reflector - Reflection analysis based on ground truth"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=Settings.GEMINI_MODEL,
            # temperature uses model default, consistent with main system
            max_output_tokens=16384,  # consistent with main system
            google_api_key=Settings.GOOGLE_API_KEY
        )
    
    def reflect(self, verdict: Verdict, feedback: HumanFeedback) -> WarmupKeyInsight:
        """Execute supervised reflection analysis (requires HumanFeedback)"""
        
        # Build prompt
        prompt_text = WARMUP_REFLECTOR_PROMPT.format(
            verdict_json=verdict.model_dump_json(indent=2),
            feedback_json=feedback.model_dump_json(indent=2)
        )
        
        # Call LLM
        print("WarmupReflector is reflecting...")
        response = self.llm.invoke(prompt_text)
        
        # Parse output
        try:
            content = response.content
            
            # Clean markdown wrapper
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            insight_data = json.loads(json_str)
            
            # Map Chinese error types to English if needed
            error_type_mapping = {
                "假阳性": "false_positive",
                "假阴性": "false_negative",
                "推理不足": "insufficient_reasoning",
                "证据不足": "insufficient_evidence",
                "规则缺失": "missing_rule",
                "无明显错误": "no_obvious_error"
            }
            if insight_data.get("error_type") in error_type_mapping:
                insight_data["error_type"] = error_type_mapping[insight_data["error_type"]]
            
            # If LLM didn't return suggested_rule_intent, auto-set based on ground_truth
            if insight_data.get("suggested_rule_intent") is None and insight_data.get("suggested_action") not in ["none", "None", None, ""]:
                if feedback.ground_truth == "True":
                    insight_data["suggested_rule_intent"] = "trust"
                else:
                    insight_data["suggested_rule_intent"] = "detection"
            
            insight = WarmupKeyInsight(**insight_data)
            
            print(f"\n{'='*60}")
            print(f"WarmupReflector Reflection Analysis")
            print(f"{'='*60}")
            print(f"Error Type: {insight.error_type}")
            print(f"Rule Intent: {insight.suggested_rule_intent}")
            print(f"Root Cause: {insight.root_cause}")
            print(f"Lesson Learned: {insight.lesson}")
            print(f"Suggested Action: {insight.suggested_action}")
            print(f"Confidence Impact: {insight.confidence_impact:+.2f}")
            
            return insight
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            print(f"Raw output:\n{response.content}")
            
            # Return default insight, set intent based on ground_truth
            default_intent = "trust" if feedback.ground_truth == "True" else "detection"
            return WarmupKeyInsight(
                error_type=None,
                suggested_rule_intent=default_intent,
                root_cause=f"Parsing failed: {str(e)}",
                lesson="Manual review required for this case",
                suggested_action="none",
                confidence_impact=0.0
            )
            
        except Exception as e:
            print(f"Reflection failed: {e}")
            print(f"Raw output: {response.content}")
            raise
