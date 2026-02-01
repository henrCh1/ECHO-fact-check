"""Verification Service - Core fact-checking logic"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal
import uuid

from agents.generator import GeneratorAgent
from agents.reflector import ReflectorAgent
from agents.curator import CuratorAgent
from utils.playbook_manager import PlaybookManager
from schemas.verdict import Verdict

from api.schemas.verify import VerifyResponse, EvidenceResponse, ProcessTraceResponse


class VerificationService:
    """Service for fact-checking operations"""
    
    def __init__(self, playbook_dir: str = "data/playbook"):
        self.playbook_dir = playbook_dir
        self.history_dir = Path("data/api_history")
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components with current playbook
        self._init_components()
    
    def _init_components(self):
        """Initialize or reinitialize agent components"""
        self.playbook_manager = PlaybookManager(playbook_dir=self.playbook_dir)
        self.generator = GeneratorAgent(playbook_manager=self.playbook_manager)
        self.reflector = ReflectorAgent()
        self.curator = CuratorAgent(playbook_manager=self.playbook_manager)
    
    def switch_playbook(self, playbook_dir: str):
        """Switch to a different playbook directory"""
        self.playbook_dir = playbook_dir
        self._init_components()
    
    def verify_claim(
        self, 
        claim: str, 
        mode: Literal["static", "evolving"] = "static"
    ) -> VerifyResponse:
        """
        Verify a single claim.
        
        Args:
            claim: The claim text to verify
            mode: 'static' - use existing rules only
                  'evolving' - trigger rule evolution after verification
        
        Returns:
            VerifyResponse with verification result
        """
        # Execute fact-checking
        verdict: Verdict = self.generator.execute(claim)
        
        # If evolving mode, run the reflection and curation loop
        if mode == "evolving":
            try:
                # Reflect on the verdict
                insight = self.reflector.reflect(verdict)
                
                # Curate: Generate and apply rule updates
                delta = self.curator.curate(
                    insight, 
                    verdict.case_id,
                    verdict_value=verdict.verdict
                )
                self.curator.apply_update(delta)
            except Exception as e:
                print(f"Evolution step failed (non-critical): {e}")
        
        # Build response
        response = self._verdict_to_response(verdict, mode)
        
        # Save to history
        self._save_to_history(response)
        
        return response
    
    def _verdict_to_response(self, verdict: Verdict, mode: str) -> VerifyResponse:
        """Convert internal Verdict to API response"""
        
        # Convert evidence
        evidence_list = [
            EvidenceResponse(
                source=e.source,
                content=e.content,
                credibility=e.credibility
            )
            for e in verdict.evidence
        ]
        
        # Convert process trace
        process_trace = None
        if verdict.process_trace:
            process_trace = ProcessTraceResponse(
                planner_output=verdict.process_trace.planner_output,
                investigator_output=verdict.process_trace.investigator_output,
                judge_reasoning=verdict.process_trace.judge_reasoning
            )
        
        return VerifyResponse(
            case_id=verdict.case_id,
            claim=verdict.claim,
            verdict=verdict.verdict,
            confidence=verdict.confidence,
            reasoning=verdict.reasoning,
            evidence=evidence_list,
            used_rules=verdict.used_rules,
            rule_match_quality=verdict.rule_match_quality,
            process_trace=process_trace,
            timestamp=verdict.timestamp,
            mode=mode
        )
    
    def _save_to_history(self, response: VerifyResponse):
        """Save verification result to history"""
        history_file = self.history_dir / f"{response.case_id}.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(response.model_dump(), f, ensure_ascii=False, indent=2, default=str)
    
    def get_verification_by_id(self, case_id: str) -> Optional[VerifyResponse]:
        """Get a verification result by case ID"""
        history_file = self.history_dir / f"{case_id}.json"
        if not history_file.exists():
            return None
        
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return VerifyResponse(**data)
