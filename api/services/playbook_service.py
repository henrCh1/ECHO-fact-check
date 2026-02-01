"""Playbook Service - Rule base management"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal, List
import shutil

from utils.playbook_manager import PlaybookManager
from api.schemas.playbook import (
    PlaybookStatusResponse, 
    RuleResponse, 
    RuleListResponse
)


class PlaybookService:
    """Service for playbook/rule base management"""
    
    # Available playbook directories
    PLAYBOOK_PATHS = {
        "default": "data/playbook",
        "warmup": "data/warmup_playbook",
    }
    
    def __init__(self, playbook_dir: str = "data/playbook"):
        self.current_playbook_name = "default"
        self.playbook_dir = playbook_dir
        self.playbook_manager = PlaybookManager(playbook_dir=playbook_dir)
    
    def get_status(self) -> PlaybookStatusResponse:
        """Get current playbook status"""
        detection = self.playbook_manager.load_detection_memory()
        trust = self.playbook_manager.load_trust_memory()
        
        detection_active = [r for r in detection.rules if r.active]
        trust_active = [r for r in trust.rules if r.active]
        
        # Get latest update time
        latest_updated = max(detection.last_updated, trust.last_updated)
        
        return PlaybookStatusResponse(
            version=f"detection:{detection.version}|trust:{trust.version}",
            detection_rules_count=len(detection_active),
            trust_rules_count=len(trust_active),
            total_active_rules=len(detection_active) + len(trust_active),
            total_cases_processed=detection.total_cases_processed + trust.total_cases_processed,
            last_updated=latest_updated
        )
    
    def get_all_rules(self) -> RuleListResponse:
        """Get all rules from both memory types"""
        detection = self.playbook_manager.load_detection_memory()
        trust = self.playbook_manager.load_trust_memory()
        
        detection_rules = [
            self._rule_to_response(r, "detection")
            for r in detection.rules if r.active
        ]
        
        trust_rules = [
            self._rule_to_response(r, "trust")
            for r in trust.rules if r.active
        ]
        
        return RuleListResponse(
            detection_rules=detection_rules,
            trust_rules=trust_rules,
            total_count=len(detection_rules) + len(trust_rules)
        )
    
    def get_rule_by_id(self, rule_id: str) -> Optional[RuleResponse]:
        """Get a specific rule by ID"""
        playbook = self.playbook_manager.load_playbook()
        
        for rule in playbook.rules:
            if rule.rule_id == rule_id and rule.active:
                return self._rule_to_response(rule, rule.memory_type or "detection")
        
        return None
    
    def switch_playbook(self, playbook_name: str, custom_path: Optional[str] = None) -> PlaybookStatusResponse:
        """Switch to a different playbook"""
        if playbook_name == "custom" and custom_path:
            new_path = custom_path
        elif playbook_name in self.PLAYBOOK_PATHS:
            new_path = self.PLAYBOOK_PATHS[playbook_name]
        else:
            raise ValueError(f"Unknown playbook: {playbook_name}")
        
        # Verify path exists
        if not Path(new_path).exists():
            raise FileNotFoundError(f"Playbook directory not found: {new_path}")
        
        self.playbook_dir = new_path
        self.current_playbook_name = playbook_name
        self.playbook_manager = PlaybookManager(playbook_dir=new_path)
        
        return self.get_status()
    
    def get_current_playbook_name(self) -> str:
        """Get the name of the currently active playbook"""
        return self.current_playbook_name
    
    def _rule_to_response(self, rule, memory_type: str) -> RuleResponse:
        """Convert internal Rule to API response"""
        return RuleResponse(
            rule_id=rule.rule_id,
            type=rule.type,
            condition=rule.condition,
            action=rule.action,
            description=rule.description,
            confidence=rule.confidence,
            evidence_count=rule.evidence_count,
            memory_type=memory_type,
            active=rule.active,
            created_from=rule.created_from,
            created_at=rule.created_at,
            parent_rule=rule.parent_rule
        )
