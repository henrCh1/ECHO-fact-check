"""Human-in-the-loop evolution service with pending buffer and review batches."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from agents.curator import CuratorAgent
from config.settings import Settings
from schemas.verdict import Verdict
from utils.playbook_manager import PlaybookManager
from warmup.agents.warmup_reflector import WarmupReflectorAgent
from warmup.schemas.feedback import HumanFeedback

from api.schemas.evolution import (
    EvolutionMetaResponse,
    PendingReviewCaseResponse,
    PendingReviewResponse,
    ReviewBatchResponse,
    ReviewBatchSubmitResponse,
    ReviewFeedbackItemRequest,
)


class EvolutionService:
    """Manage delayed human feedback for evolving mode."""

    def __init__(
        self,
        playbook_dir: str = "data/playbook",
        evolution_dir: str = "data/evolution",
        batch_size: int = 3,
    ):
        self.playbook_dir = playbook_dir
        self.batch_size = batch_size
        self.base_dir = Path(evolution_dir)
        self.pending_cases_dir = self.base_dir / "pending_cases"
        self.review_batches_dir = self.base_dir / "review_batches"
        self.feedback_history_dir = self.base_dir / "feedback_history"

        for directory in (
            self.base_dir,
            self.pending_cases_dir,
            self.review_batches_dir,
            self.feedback_history_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        self.playbook_manager = PlaybookManager(playbook_dir=playbook_dir)
        self.reflector = None
        self.curator = None
        if Settings.has_llm_config():
            self.reflector = WarmupReflectorAgent()
            self.curator = CuratorAgent(playbook_manager=self.playbook_manager)

    def enqueue_verdict(self, verdict: Verdict) -> EvolutionMetaResponse:
        """Store a verdict for later human review."""
        now = datetime.now().isoformat()
        playbook_snapshot = self.playbook_manager.load_playbook().version
        record = {
            "case_id": verdict.case_id,
            "created_at": now,
            "updated_at": now,
            "review_status": "pending",
            "batch_id": None,
            "playbook_version_snapshot": playbook_snapshot,
            "verdict_data": verdict.model_dump(mode="json"),
        }
        self._write_json(self.pending_cases_dir / f"{verdict.case_id}.json", record)
        pending_state = self.get_pending_review()
        return EvolutionMetaResponse(
            pending_count=pending_state.pending_count,
            review_batch_ready=pending_state.has_pending_batch,
            review_batch_id=pending_state.batch.batch_id if pending_state.batch else None,
        )

    def get_pending_review(self) -> PendingReviewResponse:
        """Get the current pending review batch, creating one if needed."""
        batch_record = self._get_active_batch_record()
        if batch_record is None:
            batch_record = self._maybe_create_review_batch()

        pending_count = len(self._get_pending_case_records(status="pending"))
        if batch_record is None:
            return PendingReviewResponse(
                has_pending_batch=False,
                pending_count=pending_count,
                batch=None,
            )

        return PendingReviewResponse(
            has_pending_batch=True,
            pending_count=pending_count,
            batch=self._build_batch_response(batch_record),
        )

    def skip_batch(self, batch_id: str) -> PendingReviewResponse:
        """Mark a batch as deferred without dismissing it."""
        batch_record = self._load_batch_record(batch_id)
        if batch_record is None:
            raise FileNotFoundError(f"Review batch not found: {batch_id}")

        if batch_record["status"] != "pending_review":
            raise ValueError(f"Batch {batch_id} is not pending review")

        batch_record["deferred_count"] = int(batch_record.get("deferred_count", 0)) + 1
        batch_record["updated_at"] = datetime.now().isoformat()
        self._save_batch_record(batch_record)
        return self.get_pending_review()

    def submit_feedback(
        self,
        batch_id: str,
        feedback_items: List[ReviewFeedbackItemRequest],
    ) -> ReviewBatchSubmitResponse:
        """Process user feedback and evolve the playbook using the warmup pipeline."""
        self._ensure_agents()
        batch_record = self._load_batch_record(batch_id)
        if batch_record is None:
            raise FileNotFoundError(f"Review batch not found: {batch_id}")

        if batch_record["status"] != "pending_review":
            raise ValueError(f"Batch {batch_id} is not pending review")

        feedback_map = {item.case_id: item for item in feedback_items}
        case_ids = batch_record.get("case_ids", [])
        missing_case_ids = [case_id for case_id in case_ids if case_id not in feedback_map]
        if missing_case_ids:
            raise ValueError(f"Missing feedback for cases: {missing_case_ids}")

        batch_record["status"] = "processing"
        batch_record["updated_at"] = datetime.now().isoformat()
        self._save_batch_record(batch_record)

        updates_applied = 0
        trial_rules_generated = 0
        detection_rules_generated = 0
        trust_rules_generated = 0
        feedback_history: List[Dict[str, Any]] = []

        for case_id in case_ids:
            case_record = self._load_case_record(case_id)
            if case_record is None:
                raise FileNotFoundError(f"Pending case not found: {case_id}")

            verdict = Verdict(**case_record["verdict_data"])
            request_item = feedback_map[case_id]
            feedback = self._build_human_feedback(verdict, request_item)
            insight = self.reflector.reflect(verdict, feedback)
            delta = self.curator.curate(
                insight,
                verdict.case_id,
                verdict_value=feedback.ground_truth,
            )
            self._prepare_delta_for_trial(delta, verdict.case_id)
            if delta.action != "no_action":
                updates_applied += 1
            if delta.new_rule and delta.action in {"add_rule", "refine_rule"}:
                trial_rules_generated += 1
                if delta.target_memory == "detection":
                    detection_rules_generated += 1
                elif delta.target_memory == "trust":
                    trust_rules_generated += 1
            self.curator.apply_update(delta)

            case_record["review_status"] = "reviewed"
            case_record["updated_at"] = datetime.now().isoformat()
            case_record["feedback"] = feedback.model_dump(mode="json")
            case_record["delta"] = delta.model_dump(mode="json")
            self._save_case_record(case_record)

            feedback_history.append(
                {
                    "case_id": case_id,
                    "feedback": feedback.model_dump(mode="json"),
                    "delta": delta.model_dump(mode="json"),
                }
            )

        batch_record["status"] = "completed"
        batch_record["updated_at"] = datetime.now().isoformat()
        batch_record["submitted_feedback"] = [item.model_dump(mode="json") for item in feedback_items]
        self._save_batch_record(batch_record)

        feedback_path = self.feedback_history_dir / f"{batch_id}.json"
        self._write_json(
            feedback_path,
            {
                "batch_id": batch_id,
                "submitted_at": datetime.now().isoformat(),
                "items": feedback_history,
            },
        )

        next_pending = self.get_pending_review()
        return ReviewBatchSubmitResponse(
            batch_id=batch_id,
            status="completed",
            processed_cases=len(case_ids),
            updates_applied=updates_applied,
            trial_rules_generated=trial_rules_generated,
            detection_rules_generated=detection_rules_generated,
            trust_rules_generated=trust_rules_generated,
            next_batch_ready=next_pending.has_pending_batch,
            next_batch_id=next_pending.batch.batch_id if next_pending.batch else None,
        )

    def _prepare_delta_for_trial(self, delta, case_id: str) -> None:
        """Force feedback-generated rules into trial status."""
        if not delta.new_rule:
            return

        delta.new_rule.rule_status = "trial"
        delta.new_rule.source_type = "human_reviewed_generation"
        case_ids = set(delta.new_rule.support_case_ids or [])
        case_ids.add(case_id)
        delta.new_rule.support_case_ids = sorted(case_ids)

    def _ensure_agents(self):
        """Lazily initialize reflector/curator after settings become available."""
        if self.reflector is None or self.curator is None:
            Settings.require_llm_config()
            self.reflector = WarmupReflectorAgent()
            self.curator = CuratorAgent(playbook_manager=self.playbook_manager)

    def _build_human_feedback(
        self,
        verdict: Verdict,
        request_item: ReviewFeedbackItemRequest,
    ) -> HumanFeedback:
        ground_truth = verdict.verdict if request_item.judgment_correct else self._invert_verdict(verdict.verdict)

        if request_item.judgment_correct and request_item.reasoning_correct:
            feedback_type = "correct_verdict_correct_reasoning"
        elif request_item.judgment_correct and not request_item.reasoning_correct:
            feedback_type = "correct_verdict_wrong_reasoning"
        elif not request_item.judgment_correct and request_item.reasoning_correct:
            feedback_type = "wrong_verdict_correct_reasoning"
        else:
            feedback_type = "wrong_verdict_wrong_reasoning"

        issue_text = (request_item.comment or "").strip() or None
        return HumanFeedback(
            case_id=verdict.case_id,
            ground_truth=ground_truth,
            feedback_type=feedback_type,
            specific_issue=issue_text,
            suggested_fix=issue_text,
        )

    def _invert_verdict(self, verdict: str) -> str:
        return "False" if verdict == "True" else "True"

    def _get_active_batch_record(self) -> Optional[Dict[str, Any]]:
        batch_records = []
        for path in self.review_batches_dir.glob("*.json"):
            record = self._read_json(path)
            if record and record.get("status") == "pending_review":
                batch_records.append(record)
        if not batch_records:
            return None
        batch_records.sort(key=lambda item: item.get("created_at", ""))
        return batch_records[0]

    def _maybe_create_review_batch(self) -> Optional[Dict[str, Any]]:
        pending_cases = self._get_pending_case_records(status="pending")
        if len(pending_cases) < self.batch_size:
            return None

        selected_cases = pending_cases[: self.batch_size]
        batch_id = f"batch_{uuid.uuid4().hex[:10]}"
        now = datetime.now().isoformat()
        batch_record = {
            "batch_id": batch_id,
            "status": "pending_review",
            "created_at": now,
            "updated_at": now,
            "deferred_count": 0,
            "case_ids": [case["case_id"] for case in selected_cases],
        }

        for case_record in selected_cases:
            case_record["review_status"] = "batched"
            case_record["batch_id"] = batch_id
            case_record["updated_at"] = now
            self._save_case_record(case_record)

        self._save_batch_record(batch_record)
        return batch_record

    def _build_batch_response(self, batch_record: Dict[str, Any]) -> ReviewBatchResponse:
        cases = []
        for case_id in batch_record.get("case_ids", []):
            case_record = self._load_case_record(case_id)
            if not case_record:
                continue
            verdict_data = case_record["verdict_data"]
            cases.append(PendingReviewCaseResponse(**verdict_data, mode="evolving"))

        return ReviewBatchResponse(
            batch_id=batch_record["batch_id"],
            status=batch_record["status"],
            created_at=batch_record["created_at"],
            updated_at=batch_record["updated_at"],
            deferred_count=batch_record.get("deferred_count", 0),
            cases=cases,
        )

    def _get_pending_case_records(self, status: str) -> List[Dict[str, Any]]:
        case_records = []
        for path in self.pending_cases_dir.glob("*.json"):
            record = self._read_json(path)
            if not record:
                continue
            if record.get("review_status") == status:
                case_records.append(record)
        case_records.sort(key=lambda item: item.get("created_at", ""))
        return case_records

    def _load_case_record(self, case_id: str) -> Optional[Dict[str, Any]]:
        return self._read_json(self.pending_cases_dir / f"{case_id}.json")

    def _save_case_record(self, record: Dict[str, Any]) -> None:
        self._write_json(self.pending_cases_dir / f"{record['case_id']}.json", record)

    def _load_batch_record(self, batch_id: str) -> Optional[Dict[str, Any]]:
        return self._read_json(self.review_batches_dir / f"{batch_id}.json")

    def _save_batch_record(self, record: Dict[str, Any]) -> None:
        self._write_json(self.review_batches_dir / f"{record['batch_id']}.json", record)

    def _read_json(self, path: Path) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _write_json(self, path: Path, data: Dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
