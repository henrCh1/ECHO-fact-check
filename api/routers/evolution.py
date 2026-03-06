"""Evolution Router - human-in-the-loop review endpoints."""

from fastapi import APIRouter, HTTPException

from api.schemas.evolution import (
    PendingReviewResponse,
    ReviewBatchSubmitRequest,
    ReviewBatchSubmitResponse,
)
from api.services.evolution_service import EvolutionService

router = APIRouter(prefix="/api/evolution", tags=["Evolution"])

evolution_service = EvolutionService()


@router.get("/pending", response_model=PendingReviewResponse)
async def get_pending_review():
    """Get the current pending review batch, if any."""
    try:
        return evolution_service.get_pending_review()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batches/{batch_id}/submit", response_model=ReviewBatchSubmitResponse)
async def submit_review_batch(batch_id: str, request: ReviewBatchSubmitRequest):
    """Submit human feedback for a buffered review batch."""
    try:
        return evolution_service.submit_feedback(batch_id, request.feedback)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batches/{batch_id}/skip", response_model=PendingReviewResponse)
async def skip_review_batch(batch_id: str):
    """Defer a pending review batch for later."""
    try:
        return evolution_service.skip_batch(batch_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
