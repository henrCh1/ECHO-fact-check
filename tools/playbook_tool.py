"""Playbook operation tools (mainly for internal system use)"""
from langchain_core.tools import tool
from utils.playbook_manager import PlaybookManager

playbook_manager = PlaybookManager()

@tool
def get_active_rules() -> str:
    """Get current active rules list (merged from both detection and trust memories)"""
    return playbook_manager.get_rules_summary()

@tool
def search_rule_by_id(rule_id: str) -> str:
    """Search for rule details by ID in both detection and trust memories"""
    # Search in detection memory
    detection = playbook_manager.load_detection_memory()
    for rule in detection.rules:
        if rule.rule_id == rule_id:
            return f"""
Rule ID: {rule.rule_id}
Memory Type: DETECTION (for false information)
Type: {rule.type}
Condition: {rule.condition}
Action: {rule.action}
Confidence: {rule.confidence}
Description: {rule.description}
            """.strip()
    
    # Search in trust memory
    trust = playbook_manager.load_trust_memory()
    for rule in trust.rules:
        if rule.rule_id == rule_id:
            return f"""
Rule ID: {rule.rule_id}
Memory Type: TRUST (for true information)
Type: {rule.type}
Condition: {rule.condition}
Action: {rule.action}
Confidence: {rule.confidence}
Description: {rule.description}
            """.strip()
    
    return f"Rule not found: {rule_id}"

# Tool list
playbook_tools = [get_active_rules, search_rule_by_id]
