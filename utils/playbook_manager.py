import json
from pathlib import Path
from typing import Optional, Literal
from datetime import datetime
import shutil

from schemas.playbook import Playbook, Rule, DeltaUpdate

class PlaybookManager:
    """Playbook Manager: Handles dual memory system (detection + trust)"""
    
    def __init__(self, playbook_dir: str = "data/playbook", use_empty_playbook: bool = False):
        self.playbook_dir = Path(playbook_dir)
        self.detection_memory_file = self.playbook_dir / "detection_memory.json"
        self.trust_memory_file = self.playbook_dir / "trust_memory.json"
        self.history_dir = self.playbook_dir / "history"
        self.use_empty_playbook = use_empty_playbook
        
        # Ensure directories exist
        self.playbook_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(exist_ok=True)
        
        # Initialize playbooks if not exist
        if not self.detection_memory_file.exists() or not self.trust_memory_file.exists():
            self._initialize_playbook()
    
    def _initialize_playbook(self) -> None:
        """Initialize dual memory playbooks (both empty)"""
        # Always start with empty rule bases for dual memory system
        initial_rules = []
        print("✅ Initializing dual memory system with empty rule bases (0 rules each)")
        
        # Create detection memory
        detection_playbook = Playbook(version="v1.0", rules=initial_rules)
        self._save_memory(detection_playbook, "detection", backup=False)
        
        # Create trust memory
        trust_playbook = Playbook(version="v1.0", rules=initial_rules)
        self._save_memory(trust_playbook, "trust", backup=False)
    
    def load_detection_memory(self) -> Playbook:
        """Load detection memory playbook"""
        with open(self.detection_memory_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Playbook(**data)
    
    def load_trust_memory(self) -> Playbook:
        """Load trust memory playbook"""
        with open(self.trust_memory_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Playbook(**data)
    
    def load_playbook(self) -> Playbook:
        """Load merged playbook (for Generator compatibility)"""
        detection = self.load_detection_memory()
        trust = self.load_trust_memory()
        
        # Mark rules with their memory type
        for rule in detection.rules:
            rule.memory_type = "detection"
        for rule in trust.rules:
            rule.memory_type = "trust"
        
        # Merge rules
        merged_rules = detection.rules + trust.rules
        
        # Handle datetime comparison (convert to naive datetimes if needed)
        def to_naive(dt):
            """Convert datetime to naive (remove timezone info)"""
            if dt.tzinfo is not None:
                return dt.replace(tzinfo=None)
            return dt
        
        latest_updated = max(to_naive(detection.last_updated), to_naive(trust.last_updated))
        
        # Create merged playbook with combined version info
        merged_playbook = Playbook(
            version=f"detection:{detection.version}|trust:{trust.version}",
            rules=merged_rules,
            last_updated=latest_updated,
            total_cases_processed=detection.total_cases_processed + trust.total_cases_processed
        )
        
        return merged_playbook
    
    def _save_memory(self, playbook: Playbook, memory_type: Literal["detection", "trust"], backup: bool = True) -> None:
        """Save specific memory playbook"""
        target_file = self.detection_memory_file if memory_type == "detection" else self.trust_memory_file
        
        if backup and target_file.exists():
            # Backup to history
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.history_dir / f"{memory_type}_{playbook.version}_{timestamp}.json"
            shutil.copy(target_file, backup_file)
        
        # Save current version
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(playbook.model_dump(), f, ensure_ascii=False, indent=2, default=str)
    
    def save_playbook(self, playbook: Playbook, backup: bool = True) -> None:
        """Save Playbook (deprecated, use for backward compatibility only)"""
        # For backward compatibility, save to detection memory
        self._save_memory(playbook, "detection", backup)
    
    def apply_delta_update(self, delta: DeltaUpdate) -> Playbook:
        """Apply delta update to appropriate memory"""
        # Determine target memory
        memory_type = delta.target_memory or "detection"
        
        # Load appropriate playbook
        playbook = self.load_detection_memory() if memory_type == "detection" else self.load_trust_memory()
        
        if delta.action == "add_rule":
            # Set memory_type on the rule
            if delta.new_rule:
                delta.new_rule.memory_type = memory_type
            playbook.add_rule(delta.new_rule)
            print(f"✅ Added rule to {memory_type} memory: {delta.new_rule.rule_id}")
        
        elif delta.action == "update_rule":
            for rule in playbook.rules:
                if rule.rule_id == delta.target_rule_id:
                    for key, value in delta.update_fields.items():
                        setattr(rule, key, value)
                    print(f"✅ Updated rule in {memory_type} memory: {delta.target_rule_id}")
                    break
        
        elif delta.action == "deprecate_rule":
            for rule in playbook.rules:
                if rule.rule_id == delta.target_rule_id:
                    rule.active = False
                    print(f"⚠️ Deprecated rule in {memory_type} memory: {delta.target_rule_id}")
                    break
        
        elif delta.action == "refine_rule":
            # Refinement: add new rule, but mark parent rule
            if delta.new_rule:
                delta.new_rule.memory_type = memory_type
            playbook.add_rule(delta.new_rule)
            print(f"✅ Refined rule in {memory_type} memory: {delta.new_rule.rule_id} (parent: {delta.new_rule.parent_rule})")
        
        elif delta.action == "no_action":
            # No rule base update needed
            print(f"ℹ️  No rule base update needed: {delta.reason}")
            playbook.total_cases_processed += 1
            # Don't update version, don't backup, just save current state
            self._save_memory(playbook, memory_type, backup=False)
            return playbook
        
        # Update version number (only when there's actual update)
        old_version = playbook.version
        major, minor = old_version.replace('v', '').split('.')
        playbook.version = f"v{major}.{int(minor) + 1}"
        playbook.total_cases_processed += 1
        
        # Save
        self._save_memory(playbook, memory_type, backup=True)
        print(f"📦 {memory_type.capitalize()} memory updated: {old_version} → {playbook.version}")
        
        return playbook
    
    def get_rules_summary(self) -> str:
        """Get merged rules summary (for Generator)"""
        detection = self.load_detection_memory()
        trust = self.load_trust_memory()
        
        detection_active = [r for r in detection.rules if r.active]
        trust_active = [r for r in trust.rules if r.active]
        
        summary = f"# Current Verification Playbook (Dual Memory System)\\n\\n"
        summary += f"Detection Memory: {detection.version} ({len(detection_active)} active rules)\\n"
        summary += f"Trust Memory: {trust.version} ({len(trust_active)} active rules)\\n"
        summary += f"Total: {len(detection_active) + len(trust_active)} active rules\\n\\n"
        
        if detection_active:
            summary += "## [DETECTION MEMORY] Rules for Identifying False Information\\n\\n"
            for rule in detection_active:
                summary += f"[{rule.rule_id}] ({rule.type})\\n"
                summary += f"- Condition: {rule.condition}\\n"
                summary += f"- Action: {rule.action}\\n"
                summary += f"- Confidence: {rule.confidence:.2f}\\n"
                summary += f"- Description: {rule.description}\\n\\n"
        
        if trust_active:
            summary += "## [TRUST MEMORY] Rules for Identifying True Information\\n\\n"
            for rule in trust_active:
                summary += f"[{rule.rule_id}] ({rule.type})\\n"
                summary += f"- Condition: {rule.condition}\\n"
                summary += f"- Action: {rule.action}\\n"
                summary += f"- Confidence: {rule.confidence:.2f}\\n"
                summary += f"- Description: {rule.description}\\n\\n"
        
        return summary
    
    def get_rules_brief_summary(self) -> str:
        """
        Get brief summary of rules (only key fields for selection)
        Used by Planner to select applicable rules with minimal token usage
        
        Only includes: rule_id, type, description, memory_type, confidence
        """
        detection = self.load_detection_memory()
        trust = self.load_trust_memory()
        
        detection_active = [r for r in detection.rules if r.active]
        trust_active = [r for r in trust.rules if r.active]
        
        summary = "# Active Rules Brief Summary\n\n"
        summary += f"Detection Memory: {detection.version} | {len(detection_active)} active rules\n"
        summary += f"Trust Memory: {trust.version} | {len(trust_active)} active rules\n"
        summary += f"Total: {len(detection_active) + len(trust_active)} active rules\n\n"
        
        if detection_active:
            summary += "## [DETECTION MEMORY] - Rules for identifying FALSE information\n\n"
            for rule in detection_active:
                summary += f"- **{rule.rule_id}** [{rule.type}] (confidence: {rule.confidence:.2f})\n"
                summary += f"  {rule.description}\n\n"
        
        if trust_active:
            summary += "## [TRUST MEMORY] - Rules for identifying TRUE information\n\n"
            for rule in trust_active:
                summary += f"- **{rule.rule_id}** [{rule.type}] (confidence: {rule.confidence:.2f})\n"
                summary += f"  {rule.description}\n\n"
        
        return summary
    
    def get_rules_by_ids(self, rule_ids: list) -> str:
        """
        Get full details of rules by their IDs
        Used by Judge to apply selected rules with complete information
        
        Args:
            rule_ids: List of rule IDs, e.g., ["shr-00001", "shr-00005"]
        
        Returns:
            Formatted string with full rule details
        """
        if not rule_ids:
            return "No rules selected."
        
        detection = self.load_detection_memory()
        trust = self.load_trust_memory()
        
        # Build a dict of all active rules
        all_rules = {}
        for rule in detection.rules:
            if rule.active:
                rule.memory_type = "detection"
                all_rules[rule.rule_id] = rule
        for rule in trust.rules:
            if rule.active:
                rule.memory_type = "trust"
                all_rules[rule.rule_id] = rule
        
        # Extract selected rules
        selected_rules = []
        for rule_id in rule_ids:
            if rule_id in all_rules:
                selected_rules.append(all_rules[rule_id])
        
        if not selected_rules:
            return f"Selected rules {rule_ids} not found in active rules."
        
        # Format output
        detail = f"# Selected Rules Detail ({len(selected_rules)} rules)\n\n"
        
        for rule in selected_rules:
            detail += f"## [{rule.rule_id}] {rule.type.upper()} ({rule.memory_type.upper()} MEMORY)\n\n"
            detail += f"**Description**: {rule.description}\n\n"
            detail += f"**Condition**: {rule.condition}\n\n"
            detail += f"**Action**: {rule.action}\n\n"
            detail += f"**Confidence**: {rule.confidence:.2f} | **Evidence Count**: {rule.evidence_count}\n\n"
            detail += "---\n\n"
        
        return detail
