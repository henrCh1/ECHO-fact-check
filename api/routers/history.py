"""History Router - Verification history endpoints"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Literal
from datetime import datetime

from api.schemas.history import (
    HistoryListResponse,
    HistoryFilterParams
)
from api.schemas.verify import VerifyResponse
from api.services.history_service import HistoryService

router = APIRouter(prefix="/api/history", tags=["History"])

# Global service instance
history_service = HistoryService()


@router.get("", response_model=HistoryListResponse)
async def get_history_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    verdict: Optional[Literal["True", "False"]] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    max_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    mode: Optional[Literal["static", "evolving"]] = None,
    search: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Get paginated list of verification history.
    
    Supports filtering by:
    - **verdict**: True or False
    - **min_confidence/max_confidence**: Confidence range
    - **mode**: static or evolving
    - **search**: Search in claim text
    - **start_date/end_date**: Date range
    """
    filters = HistoryFilterParams(
        verdict=verdict,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        mode=mode,
        search=search,
        start_date=start_date,
        end_date=end_date
    )
    
    try:
        return history_service.get_history_list(page, page_size, filters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{case_id}", response_model=VerifyResponse)
async def get_history_detail(case_id: str):
    """
    Get detailed information about a specific verification record.
    """
    try:
        result = history_service.get_history_detail(case_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Record not found: {case_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{case_id}")
async def delete_history(case_id: str):
    """
    Delete a verification record from history.
    """
    try:
        success = history_service.delete_history(case_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Record not found: {case_id}")
        return {"message": f"Record {case_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
