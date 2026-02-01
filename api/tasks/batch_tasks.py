"""Batch Task Manager - Handle CSV batch verification"""
import json
import csv
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal, Dict, Any
from threading import Thread
import traceback

from api.schemas.verify import BatchTaskResponse, BatchResultItem


class BatchTaskManager:
    """Manager for batch verification tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.results_dir = Path("data/batch_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir = Path("data/batch_uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def create_task(self, csv_content: bytes, filename: str, mode: str = "static") -> BatchTaskResponse:
        """Create a new batch verification task"""
        task_id = uuid.uuid4().hex[:12]
        
        # Save uploaded file
        upload_path = self.upload_dir / f"{task_id}_{filename}"
        with open(upload_path, 'wb') as f:
            f.write(csv_content)
        
        # Count rows (excluding header)
        total = 0
        try:
            with open(upload_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                total = sum(1 for _ in reader)
        except Exception:
            total = 0
        
        task = BatchTaskResponse(
            task_id=task_id,
            status="pending",
            total=total,
            completed=0,
            failed=0,
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = {
            "task": task,
            "upload_path": str(upload_path),
            "mode": mode,
            "results": []
        }
        
        return task
    
    def get_task(self, task_id: str) -> Optional[BatchTaskResponse]:
        """Get task status"""
        task_data = self.tasks.get(task_id)
        if not task_data:
            # Try to load from disk
            result_file = self.results_dir / f"{task_id}_status.json"
            if result_file.exists():
                with open(result_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return BatchTaskResponse(**data)
            return None
        return task_data["task"]
    
    def update_task(self, task_id: str, **kwargs):
        """Update task status"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]["task"]
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        task.updated_at = datetime.now()
        
        # Persist status
        self._save_task_status(task_id)
    
    def add_result(self, task_id: str, result: BatchResultItem):
        """Add a result item"""
        if task_id in self.tasks:
            self.tasks[task_id]["results"].append(result)
    
    def run_batch_verification(self, task_id: str):
        """
        Run batch verification (called from background thread).
        """
        task_data = self.tasks.get(task_id)
        if not task_data:
            return
        
        upload_path = task_data["upload_path"]
        mode = task_data["mode"]
        
        try:
            self.update_task(task_id, status="running")
            
            # Import verification service
            from api.services.verification_service import VerificationService
            service = VerificationService()
            
            # Read CSV
            with open(upload_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Find claim column (flexible naming)
            claim_column = None
            for col in ['claim', 'Claim', 'statement', 'Statement', 'text', 'Text']:
                if col in (rows[0].keys() if rows else []):
                    claim_column = col
                    break
            
            if not claim_column and rows:
                # Use first column
                claim_column = list(rows[0].keys())[0]
            
            completed = 0
            failed = 0
            
            for idx, row in enumerate(rows):
                try:
                    claim = row.get(claim_column, '')
                    if not claim.strip():
                        continue
                    
                    # Verify
                    response = service.verify_claim(claim, mode=mode)
                    
                    result = BatchResultItem(
                        row_number=idx + 2,  # 1-based, skip header
                        claim=claim,
                        verdict=response.verdict,
                        confidence=response.confidence,
                        reasoning=response.reasoning,
                        status="success"
                    )
                    completed += 1
                    
                except Exception as e:
                    result = BatchResultItem(
                        row_number=idx + 2,
                        claim=row.get(claim_column, ''),
                        status="failed",
                        error=str(e)
                    )
                    failed += 1
                
                self.add_result(task_id, result)
                self.update_task(task_id, completed=completed, failed=failed)
            
            self.update_task(task_id, status="completed")
            self._save_results(task_id)
            
        except Exception as e:
            self.update_task(
                task_id,
                status="failed",
                error_message=str(e)
            )
            traceback.print_exc()
    
    def start_background_task(self, task_id: str):
        """Start batch verification in background thread"""
        thread = Thread(target=self.run_batch_verification, args=(task_id,))
        thread.daemon = True
        thread.start()
    
    def get_results_file(self, task_id: str) -> Optional[Path]:
        """Get path to results CSV file"""
        result_file = self.results_dir / f"{task_id}_results.csv"
        if result_file.exists():
            return result_file
        return None
    
    def _save_task_status(self, task_id: str):
        """Persist task status to disk"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]["task"]
        status_file = self.results_dir / f"{task_id}_status.json"
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(task.model_dump(), f, ensure_ascii=False, indent=2, default=str)
    
    def _save_results(self, task_id: str):
        """Save results to CSV file"""
        if task_id not in self.tasks:
            return
        
        results = self.tasks[task_id]["results"]
        result_file = self.results_dir / f"{task_id}_results.csv"
        
        with open(result_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['row_number', 'claim', 'verdict', 'confidence', 'reasoning', 'status', 'error'])
            
            for r in results:
                writer.writerow([
                    r.row_number,
                    r.claim,
                    r.verdict or '',
                    r.confidence or '',
                    r.reasoning or '',
                    r.status,
                    r.error or ''
                ])


# Global instance
batch_task_manager = BatchTaskManager()
