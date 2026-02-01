"""History Service - Verification history management"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import os

from api.schemas.history import (
    HistoryItemSummary,
    HistoryListResponse,
    HistoryFilterParams
)
from api.schemas.verify import VerifyResponse


class HistoryService:
    """Service for managing verification history"""
    
    def __init__(self, history_dir: str = "data/api_history"):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def get_history_list(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[HistoryFilterParams] = None
    ) -> HistoryListResponse:
        """Get paginated history list with optional filters"""
        
        # Load all history files
        all_items = []
        for file_path in self.history_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_items.append(data)
            except Exception:
                continue
        
        # Sort by timestamp (newest first)
        all_items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply filters
        if filters:
            all_items = self._apply_filters(all_items, filters)
        
        # Calculate pagination
        total = len(all_items)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Get page items
        page_items = all_items[start_idx:end_idx]
        
        # Convert to summary items
        summary_items = [
            HistoryItemSummary(
                case_id=item['case_id'],
                claim_summary=item['claim'][:100] + ('...' if len(item['claim']) > 100 else ''),
                verdict=item['verdict'],
                confidence=item['confidence'],
                rule_match_quality=item.get('rule_match_quality', 'none'),
                timestamp=datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00')) if isinstance(item['timestamp'], str) else item['timestamp'],
                mode=item.get('mode', 'static')
            )
            for item in page_items
        ]
        
        return HistoryListResponse(
            items=summary_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    def get_history_detail(self, case_id: str) -> Optional[VerifyResponse]:
        """Get detailed history record by case ID"""
        file_path = self.history_dir / f"{case_id}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return VerifyResponse(**data)
    
    def delete_history(self, case_id: str) -> bool:
        """Delete a history record"""
        file_path = self.history_dir / f"{case_id}.json"
        
        if not file_path.exists():
            return False
        
        os.remove(file_path)
        return True
    
    def get_stats(self) -> dict:
        """Get history statistics"""
        all_items = []
        for file_path in self.history_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_items.append(json.load(f))
            except Exception:
                continue
        
        total = len(all_items)
        if total == 0:
            return {
                "total_verifications": 0,
                "true_count": 0,
                "false_count": 0,
                "avg_confidence": 0,
                "static_mode_count": 0,
                "evolving_mode_count": 0
            }
        
        true_count = sum(1 for item in all_items if item.get('verdict') == 'True')
        false_count = sum(1 for item in all_items if item.get('verdict') == 'False')
        avg_confidence = sum(item.get('confidence', 0) for item in all_items) / total
        static_count = sum(1 for item in all_items if item.get('mode', 'static') == 'static')
        evolving_count = sum(1 for item in all_items if item.get('mode') == 'evolving')
        
        return {
            "total_verifications": total,
            "true_count": true_count,
            "false_count": false_count,
            "avg_confidence": round(avg_confidence, 4),
            "static_mode_count": static_count,
            "evolving_mode_count": evolving_count
        }
    
    def _apply_filters(self, items: List[dict], filters: HistoryFilterParams) -> List[dict]:
        """Apply filters to history items"""
        filtered = items
        
        if filters.verdict:
            filtered = [i for i in filtered if i.get('verdict') == filters.verdict]
        
        if filters.min_confidence is not None:
            filtered = [i for i in filtered if i.get('confidence', 0) >= filters.min_confidence]
        
        if filters.max_confidence is not None:
            filtered = [i for i in filtered if i.get('confidence', 1) <= filters.max_confidence]
        
        if filters.mode:
            filtered = [i for i in filtered if i.get('mode', 'static') == filters.mode]
        
        if filters.search:
            search_term = filters.search.lower()
            filtered = [i for i in filtered if search_term in i.get('claim', '').lower()]
        
        if filters.start_date:
            filtered = [
                i for i in filtered 
                if i.get('timestamp') and 
                datetime.fromisoformat(i['timestamp'].replace('Z', '+00:00')) >= filters.start_date
            ]
        
        if filters.end_date:
            filtered = [
                i for i in filtered 
                if i.get('timestamp') and 
                datetime.fromisoformat(i['timestamp'].replace('Z', '+00:00')) <= filters.end_date
            ]
        
        return filtered
