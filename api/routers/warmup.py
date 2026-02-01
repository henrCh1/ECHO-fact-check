"""Warmup Router - Custom playbook generation endpoints"""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from threading import Thread

from api.schemas.warmup import (
    WarmupStartRequest,
    WarmupTaskResponse,
    WarmupDatasetInfo
)
from api.services.warmup_service import WarmupService

router = APIRouter(prefix="/api/warmup", tags=["Warmup"])

# Global service instance
warmup_service = WarmupService()


@router.post("/start", response_model=WarmupTaskResponse)
async def start_warmup(
    request: WarmupStartRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a warmup process to generate a custom playbook.
    
    - **dataset_path**: Path to CSV file. If None, uses default data/warmup.csv
    - **output_playbook_name**: Name for the generated playbook directory
    
    The warmup process runs in background. Use GET /api/warmup/{task_id} to check progress.
    """
    try:
        task = warmup_service.create_task(
            dataset_path=request.dataset_path,
            output_name=request.output_playbook_name
        )
        
        # Start warmup in background thread
        thread = Thread(target=warmup_service.run_warmup, args=(task.task_id,))
        thread.daemon = True
        thread.start()
        
        return task
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=WarmupTaskResponse)
async def get_warmup_status(task_id: str):
    """
    Get the status of a warmup task.
    """
    task = warmup_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/upload", response_model=WarmupDatasetInfo)
async def upload_warmup_dataset(file: UploadFile = File(...)):
    """
    Upload a custom warmup dataset CSV file.
    
    Required columns:
    - Statement: The claim text
    - Rating: True or False
    - Full_Analysis: Complete fact-check analysis
    
    Returns dataset info including the file path to use in /start endpoint.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        content = await file.read()
        info = warmup_service.upload_dataset(content, file.filename)
        return info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
