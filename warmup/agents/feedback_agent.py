"""FeedbackAgent: Automated Human Feedback Simulator - 2-class version"""

from langchain_google_genai import ChatGoogleGenerativeAI
import json
from typing import Dict, Any

from schemas.verdict import Verdict
from warmup.schemas.feedback import HumanFeedback
from config.settings import Settings


class FeedbackAgent:
    """Automated Feedback Agent - Simulates human expert feedback (2-class version)"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=Settings.GEMINI_MODEL,
            # temperature uses model default, consistent with main system
            max_output_tokens=16384,  # consistent with main system
            google_api_key=Settings.GOOGLE_API_KEY
        )
        self.prompt_template = self._build_prompt_template()
    
    def _build_prompt_template(self) -> str:
        """Build feedback prompt template"""
        return """You are a professional fact-checking expert responsible for evaluating AI system verification results.

# Your Task
Based on the standard answer and complete analysis, evaluate AgentA's verification results and provide structured feedback.

# AgentA's Verification Result
```json
{verdict_json}
```

# Standard Answer
- Rating: {rating}

# Complete Expert Analysis
{full_analysis}

# Feedback Requirements
Please carefully compare AgentA's results with the standard answer and answer the following questions:

## 1. Verdict Correctness
AgentA's verdict is "{agent_verdict}", the standard answer is "{rating}".
Are they consistent?

## 2. Reasoning Process Evaluation
Read AgentA's reasoning and expert's full_analysis, evaluate:
- Is AgentA's reasoning logic rigorous?
- Were any key information missed?
- Are there any logic jumps or incorrect assumptions?

## 3. Specific Problem Diagnosis (if there are errors)
If AgentA's verdict or reasoning has problems, diagnose:
- Where did the reasoning logic break?
- Was background information ignored?
- Was the wrong source checked?
- Were critical rules misused or not used?

## 4. Improvement Suggestions
Based on problem diagnosis, provide specific improvement suggestions:
- What rules need to be added?
- Which existing rules need modification?
- How should similar situations be handled next time?

# Output Format
Please output a JSON object in the following format:
{{
  "ground_truth": "True/False",
  "feedback_type": "correct_verdict_correct_reasoning/correct_verdict_wrong_reasoning/wrong_verdict_correct_reasoning/wrong_verdict_wrong_reasoning",
  "specific_issue": "Specific problem description, null if no problems",
  "suggested_fix": "Improvement suggestion, null if no problems"
}}

Output must be pure JSON without any markdown tags or other text.

Please begin analysis and output feedback:
"""
    
    def generate_feedback(
        self, 
        verdict: Verdict, 
        rating: str, 
        full_analysis: str
    ) -> HumanFeedback:
        """Generate automated feedback"""
        
        # Normalize rating format (2-class)
        rating_normalized = self._normalize_rating(rating)
        
        # Build prompt
        prompt_text = self.prompt_template.format(
            verdict_json=verdict.model_dump_json(indent=2),
            rating=rating_normalized,
            full_analysis=full_analysis,
            agent_verdict=verdict.verdict
        )
        
        # Call LLM
        print("FeedbackAgent is generating feedback...")
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
            
            # Sanitize JSON string to handle unescaped control characters
            json_str = self._sanitize_json_string(json_str)
            
            feedback_data = json.loads(json_str)
            
            # Force use normalized ground_truth (ensure 2-class)
            feedback_data["ground_truth"] = rating_normalized
            
            # Map Chinese feedback types to English if needed
            feedback_type = feedback_data.get("feedback_type", "")
            feedback_type_mapping = {
                "判断正确_推理正确": "correct_verdict_correct_reasoning",
                "判断正确_推理错误": "correct_verdict_wrong_reasoning",
                "判断错误_推理正确": "wrong_verdict_correct_reasoning",
                "判断错误_推理错误": "wrong_verdict_wrong_reasoning"
            }
            if feedback_type in feedback_type_mapping:
                feedback_data["feedback_type"] = feedback_type_mapping[feedback_type]
            
            # Create HumanFeedback object
            feedback = HumanFeedback(
                case_id=verdict.case_id,
                ground_truth=feedback_data["ground_truth"],
                feedback_type=feedback_data["feedback_type"],
                specific_issue=feedback_data.get("specific_issue"),
                suggested_fix=feedback_data.get("suggested_fix")
            )
            
            print(f"\n{'='*60}")
            print(f"FeedbackAgent Feedback")
            print(f"{'='*60}")
            print(f"Ground Truth: {feedback.ground_truth}")
            print(f"Feedback Type: {feedback.feedback_type}")
            if feedback.specific_issue:
                print(f"Specific Issue: {feedback.specific_issue}")
            if feedback.suggested_fix:
                print(f"Suggested Fix: {feedback.suggested_fix}")
            
            return feedback
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            print(f"Raw output:\n{response.content}")
            
            # Return default feedback
            return HumanFeedback(
                case_id=verdict.case_id,
                ground_truth=rating_normalized,
                feedback_type="wrong_verdict_wrong_reasoning",
                specific_issue=f"FeedbackAgent parsing failed: {str(e)}",
                suggested_fix="Manual review required for this case"
            )
            
        except Exception as e:
            print(f"Failed to generate feedback: {e}")
            print(f"Raw output: {response.content}")
            raise
    
    def _sanitize_json_string(self, json_str: str) -> str:
        """Sanitize JSON string to handle unescaped control characters from LLM output
        
        The LLM sometimes generates JSON with literal newlines, tabs, etc. in string values
        instead of properly escaped sequences (\n, \t, etc.). This method fixes those issues.
        """
        try:
            # First attempt: try parsing as-is
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            # If parsing fails, attempt to fix common issues
            # Replace literal control characters within string values
            # This is a simple heuristic that works for most cases
            
            # Replace unescaped newlines, tabs, carriage returns, form feeds
            sanitized = json_str.replace('\n', '\\n')
            sanitized = sanitized.replace('\r', '\\r')
            sanitized = sanitized.replace('\t', '\\t')
            sanitized = sanitized.replace('\f', '\\f')
            
            return sanitized
    
    def _normalize_rating(self, rating: str) -> str:
        """Normalize rating format - 2-class version (True/False only)"""
        rating_lower = rating.lower().strip()
        
        if rating_lower in ['true', 'correct', 'accurate', 'yes', 'supported']:
            return "True"
        else:
            # All non-True are classified as False (including Unverifiable)
            return "False"
