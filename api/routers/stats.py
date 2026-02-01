"""Stats Router - System statistics endpoints"""
from fastapi import APIRouter, HTTPException

from api.services.history_service import HistoryService
from api.services.playbook_service import PlaybookService

router = APIRouter(prefix="/api/stats", tags=["Statistics"])

# Global service instances
history_service = HistoryService()
playbook_service = PlaybookService()


@router.get("")
async def get_system_stats():
    """
    Get comprehensive system statistics.
    
    Returns:
    - Verification statistics (total, verdicts, confidence)
    - Playbook statistics (rules count, version)
    """
    try:
        # Get history stats
        verification_stats = history_service.get_stats()
        
        # Get playbook stats
        playbook_status = playbook_service.get_status()
        
        return {
            "verification": verification_stats,
            "playbook": {
                "version": playbook_status.version,
                "detection_rules_count": playbook_status.detection_rules_count,
                "trust_rules_count": playbook_status.trust_rules_count,
                "total_active_rules": playbook_status.total_active_rules,
                "total_cases_processed": playbook_status.total_cases_processed,
                "last_updated": playbook_status.last_updated
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
