"""AgentB: Reflector - Benchmark Version (No Human Feedback Required)"""

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import Literal, Optional
import json

from schemas.verdict import Verdict
from config.settings import Settings
from prompts.reflector_prompt import REFLECTOR_PROMPT
from utils.llm_response import content_to_text, extract_json_text

class KeyInsight(BaseModel):
    """Key insight output from Reflector"""
    error_type: Optional[Literal["false_positive", "false_negative", "insufficient_reasoning", "insufficient_evidence", "missing_rule", "planning_error", "no_obvious_error"]] = None
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

class ReflectorAgent:
    """AgentB: Reflector - Self-reflection based on reasoning process"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=Settings.GEMINI_MODEL,
            # temperature=0.1,  # Commented out to use model's default
            max_output_tokens=16384,
            google_api_key=Settings.GOOGLE_API_KEY
        )
        self.prompt_template = REFLECTOR_PROMPT
    
    def reflect(self, verdict: Verdict) -> KeyInsight:
        """Execute reflection analysis (no human feedback required)"""
        
        # Build prompt
        prompt_text = self.prompt_template.format(
            verdict_json=verdict.model_dump_json(indent=2)
        )
        
        # Call LLM
        print("🔄 AgentB is reflecting...")
        response = self.llm.invoke(prompt_text)
        
        # Parse output
        try:
            json_str = extract_json_text(response.content)
            insight_data = json.loads(json_str)
            insight = KeyInsight(**insight_data)
            
            print(f"\n{'='*60}")
            print(f"🔍 AgentB Reflection Analysis")
            print(f"{'='*60}")
            print(f"Error Type: {insight.error_type}")
            print(f"Root Cause: {insight.root_cause}")
            print(f"Lesson Learned: {insight.lesson}")
            print(f"Suggested Action: {insight.suggested_action}")
            print(f"Confidence Impact: {insight.confidence_impact:+.2f}")
            
            return insight
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Raw output:\n{content_to_text(response.content)}")
            
            # Return default insight
            return KeyInsight(
                error_type="no_obvious_error",
                root_cause=f"Parsing failed: {str(e)}",
                lesson="Manual review required for this case",
                suggested_action="None",
                confidence_impact=0.0
            )
            
        except Exception as e:
            print(f"❌ Reflection failed: {e}")
            print(f"Raw output: {content_to_text(response.content)}")
            raise
