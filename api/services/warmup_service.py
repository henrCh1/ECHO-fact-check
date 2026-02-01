"""Warmup Service - Custom playbook generation"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid
import csv
import shutil

from utils.playbook_manager import PlaybookManager
from api.schemas.warmup import WarmupTaskResponse, WarmupDatasetInfo


class WarmupService:
    """Service for warmup/custom playbook generation"""
    
    def __init__(self):
        self.upload_dir = Path("data/warmup_uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        self.custom_playbook_base = Path("data/custom_playbooks")
        self.custom_playbook_base.mkdir(parents=True, exist_ok=True)
        
        # Task storage (in-memory, could be replaced with Redis/DB)
        self.tasks = {}
    
    def upload_dataset(self, file_content: bytes, filename: str) -> WarmupDatasetInfo:
        """Upload and validate a warmup dataset CSV"""
        # Save file
        file_path = self.upload_dir / f"{uuid.uuid4().hex}_{filename}"
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Parse and validate
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                columns = reader.fieldnames or []
        except Exception as e:
            raise ValueError(f"Invalid CSV file: {e}")
        
        # Validate required columns
        required_cols = {'Statement', 'Rating', 'Full_Analysis'}
        if not required_cols.issubset(set(columns)):
            missing = required_cols - set(columns)
            raise ValueError(f"Missing required columns: {missing}")
        
        # Get sample claims
        sample_claims = [row.get('Statement', '')[:100] for row in rows[:3]]
        
        return WarmupDatasetInfo(
            filename=str(file_path),
            total_rows=len(rows),
            columns=columns,
            sample_claims=sample_claims
        )
    
    def create_task(
        self, 
        dataset_path: Optional[str] = None,
        output_name: str = "custom"
    ) -> WarmupTaskResponse:
        """Create a new warmup task"""
        task_id = uuid.uuid4().hex[:12]
        
        # Determine dataset path
        actual_dataset_path = dataset_path or "data/warmup.csv"
        
        # Count total cases
        total_cases = 0
        try:
            with open(actual_dataset_path, 'r', encoding='utf-8') as f:
                total_cases = sum(1 for _ in f) - 1  # Subtract header
        except Exception:
            total_cases = 0
        
        # Create output directory
        output_dir = self.custom_playbook_base / output_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        task = WarmupTaskResponse(
            task_id=task_id,
            status="pending",
            total_cases=total_cases,
            processed_cases=0,
            correct_verdicts=0,
            incorrect_verdicts=0,
            rules_generated=0,
            detection_rules=0,
            trust_rules=0,
            created_at=datetime.now(),
            output_playbook_path=str(output_dir)
        )
        
        self.tasks[task_id] = {
            "task": task,
            "dataset_path": actual_dataset_path,
            "output_dir": str(output_dir)
        }
        
        return task
    
    def get_task(self, task_id: str) -> Optional[WarmupTaskResponse]:
        """Get task status by ID"""
        task_data = self.tasks.get(task_id)
        if not task_data:
            return None
        return task_data["task"]
    
    def update_task(self, task_id: str, **kwargs):
        """Update task progress"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]["task"]
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        task.updated_at = datetime.now()
    
    def run_warmup(self, task_id: str):
        """
        Run the warmup process (called from background task).
        This imports and runs the warmup system.
        """
        task_data = self.tasks.get(task_id)
        if not task_data:
            return
        
        dataset_path = task_data["dataset_path"]
        output_dir = task_data["output_dir"]
        
        try:
            self.update_task(task_id, status="running")
            
            # Import warmup components
            from warmup.warmup_main import WarmupFactCheckSystem
            
            # Create a modified warmup system that uses our output directory
            # and reports progress back to us
            system = WarmupFactCheckSystem(dataset_path=dataset_path)
            
            # Override the playbook directory
            system.playbook_manager = PlaybookManager(
                playbook_dir=output_dir,
                use_empty_playbook=True
            )
            
            # Run the warmup (this is blocking)
            system.run_full_dataset()
            
            # Get final stats
            playbook = system.playbook_manager.load_playbook()
            detection_count = len([r for r in playbook.rules if r.active and r.memory_type == "detection"])
            trust_count = len([r for r in playbook.rules if r.active and r.memory_type == "trust"])
            
            self.update_task(
                task_id,
                status="completed",
                processed_cases=system.stats["total_cases"],
                correct_verdicts=system.stats["correct_verdicts"],
                incorrect_verdicts=system.stats["incorrect_verdicts"],
                rules_generated=len(playbook.get_active_rules()),
                detection_rules=detection_count,
                trust_rules=trust_count
            )
            
        except Exception as e:
            self.update_task(
                task_id,
                status="failed",
                error_message=str(e)
            )
