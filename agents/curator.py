from langchain_google_genai import ChatGoogleGenerativeAI
import json
from datetime import datetime

from schemas.playbook import Rule, DeltaUpdate
from agents.reflector import KeyInsight
from utils.playbook_manager import PlaybookManager
from prompts.curator_prompt import CURATOR_PROMPT
from config.settings import Settings

class CuratorAgent:
    """AgentC: Curator - Transform insights into rule updates"""
    
    def __init__(self, playbook_manager: PlaybookManager = None):
        self.llm = ChatGoogleGenerativeAI(
            model=Settings.GEMINI_MODEL,
            # temperature=0.1,  # Commented out to use model's default
            max_output_tokens=16384,
            google_api_key=Settings.GOOGLE_API_KEY
        )
        self.playbook_manager = playbook_manager if playbook_manager else PlaybookManager()
    
    def curate(self, insight: KeyInsight, case_id: str, verdict_value: str = "False") -> DeltaUpdate:
        """Generate rule updates with automatic memory classification
        
        Args:
            insight: Reflection insight from ReflectorAgent
            case_id: Case ID for tracking
            verdict_value: Verdict from the case ("True" or "False")
                          Used for automatic memory classification
        """
        
        # Get current rules (Brief Summary for token optimization)
        current_rules = self.playbook_manager.get_rules_brief_summary()
        
        # Build prompt
        prompt_text = CURATOR_PROMPT.format(
            current_rules=current_rules,
            insight_json=insight.model_dump_json(indent=2)
        )
        
        # Call LLM
        print("AgentC is curating...")
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
            
            delta_data = json.loads(json_str)
            
            # If adding new rule, supplement created_from field and fix invalid type
            if delta_data.get("new_rule"):
                delta_data["new_rule"]["created_from"] = case_id
                delta_data["new_rule"]["created_at"] = datetime.now().isoformat()
                
                # Auto-fix invalid rule type (LLM sometimes generates 'meta' which is not allowed)
                valid_types = ["strategy", "tool_template", "pitfall"]
                if delta_data["new_rule"].get("type") not in valid_types:
                    print(f"   ⚠️ Auto-fixing invalid rule type: '{delta_data['new_rule'].get('type')}' → 'strategy'")
                    delta_data["new_rule"]["type"] = "strategy"
            
            # ============================================================
            # SCRIPT-BASED MEMORY CLASSIFICATION
            # Automatically classify rules based on verdict
            # ============================================================
            if delta_data.get("action") in ["add_rule", "refine_rule", "update_rule", "deprecate_rule"]:
                # Determine target memory based on verdict
                if verdict_value == "True":
                    target_memory = "trust"
                    print(f"   🔵 Auto-classified to TRUST memory (verdict: True)")
                else:  # "False" or "Unverifiable"
                    target_memory = "detection"
                    print(f"   🔴 Auto-classified to DETECTION memory (verdict: {verdict_value})")
                
                delta_data["target_memory"] = target_memory
            else:  # no_action
                # Default to detection for no_action
                delta_data["target_memory"] = "detection"
            
            delta = DeltaUpdate(**delta_data)
            
            print(f"\n{'='*60}")
            print(f"AgentC Generated Update")
            print(f"{'='*60}")
            print(f"Action Type: {delta.action}")
            print(f"Target Memory: {delta.target_memory}")
            print(f"Reason: {delta.reason}")
            if delta.new_rule:
                print(f"New Rule ID: {delta.new_rule.rule_id}")
            if delta.target_rule_id:
                print(f"Target Rule: {delta.target_rule_id}")
            
            return delta
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            print(f"Raw output:\n{response.content[:500]}...")
            
            # Return no_action as fallback
            return DeltaUpdate(
                action="no_action",
                reason=f"JSON parsing failed: {str(e)}"
            )
            
        except Exception as e:
            print(f"Curation failed: {e}")
            print(f"Raw output: {response.content[:500]}...")
            
            # Return no_action as fallback instead of raising
            return DeltaUpdate(
                action="no_action",
                reason=f"Curation error: {str(e)}"
            )
    
    def apply_update(self, delta: DeltaUpdate) -> None:
        """Apply update to Playbook"""
        self.playbook_manager.apply_delta_update(delta)
