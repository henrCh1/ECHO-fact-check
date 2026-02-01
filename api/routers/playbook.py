"""Playbook Router - Rule base management endpoints"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from api.schemas.playbook import (
    PlaybookStatusResponse,
    RuleListResponse,
    RuleResponse,
    PlaybookSwitchRequest
)
from api.services.playbook_service import PlaybookService

router = APIRouter(prefix="/api/playbook", tags=["Playbook"])

# Global service instance
playbook_service = PlaybookService()


@router.get("", response_model=PlaybookStatusResponse)
async def get_playbook_status():
    """
    Get current playbook status including rule counts and version information.
    """
    try:
        return playbook_service.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules", response_model=RuleListResponse)
async def get_all_rules():
    """
    Get all active rules from both detection and trust memory.
    """
    try:
        return playbook_service.get_all_rules()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule_detail(rule_id: str):
    """
    Get detailed information about a specific rule.
    """
    try:
        rule = playbook_service.get_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")
        return rule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switch", response_model=PlaybookStatusResponse)
async def switch_playbook(request: PlaybookSwitchRequest):
    """
    Switch to a different playbook.
    
    - **playbook_name**: 
        - `default`: The main playbook in data/playbook
        - `warmup`: The warmup-generated playbook in data/warmup_playbook  
        - `custom`: A custom playbook (requires custom_path)
    - **custom_path**: Path to custom playbook directory (only for 'custom' type)
    """
    try:
        return playbook_service.switch_playbook(
            request.playbook_name,
            request.custom_path
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current")
async def get_current_playbook():
    """
    Get the name of the currently active playbook.
    """
    return {
        "current_playbook": playbook_service.get_current_playbook_name(),
        "playbook_dir": playbook_service.playbook_dir
    }
