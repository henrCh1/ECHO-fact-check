"""Verification Router - Core fact-checking endpoints"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import Literal

from api.schemas.verify import (
    VerifyRequest, 
    VerifyResponse, 
    BatchTaskResponse
)
from api.services.verification_service import VerificationService
from api.tasks.batch_tasks import batch_task_manager

router = APIRouter(prefix="/api/verify", tags=["Verification"])

# Global service instance
verification_service = VerificationService()


@router.post("", response_model=VerifyResponse)
async def verify_claim(request: VerifyRequest):
    """
    Verify a single claim.
    
    - **claim**: The claim text to verify
    - **mode**: 
        - `static`: Use existing rules only (faster, no rule evolution)
        - `evolving`: Trigger rule evolution after verification (learning mode)
    """
    try:
        result = verification_service.verify_claim(
            claim=request.claim,
            mode=request.mode
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchTaskResponse)
async def batch_verify(
    file: UploadFile = File(...),
    mode: Literal["static", "evolving"] = Form(default="static")
):
    """
    Upload a CSV file for batch verification.
    
    CSV should have a column named 'claim', 'Claim', 'statement', 'Statement', 'text', or 'Text'.
    The first column will be used if none of these are found.
    
    Returns a task ID that can be used to check progress and download results.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        content = await file.read()
        task = batch_task_manager.create_task(content, file.filename, mode)
        
        # Start background processing
        batch_task_manager.start_background_task(task.task_id)
        
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/{task_id}", response_model=BatchTaskResponse)
async def get_batch_status(task_id: str):
    """
    Get the status of a batch verification task.
    """
    task = batch_task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/batch/{task_id}/download")
async def download_batch_results(task_id: str):
    """
    Download the results of a completed batch verification task as CSV.
    """
    task = batch_task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Task is not completed. Current status: {task.status}"
        )
    
    result_file = batch_task_manager.get_results_file(task_id)
    if not result_file:
        raise HTTPException(status_code=404, detail="Results file not found")
    
    return FileResponse(
        result_file,
        media_type="text/csv",
        filename=f"verification_results_{task_id}.csv"
    )
