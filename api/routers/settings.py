"""Settings Router - runtime configuration endpoints."""

from fastapi import APIRouter, HTTPException

from api.schemas.settings import RuntimeSettingsResponse, RuntimeSettingsUpdateRequest
from config.settings import Settings

router = APIRouter(prefix="/api/settings", tags=["Settings"])


def _current_settings_response() -> RuntimeSettingsResponse:
    return RuntimeSettingsResponse(
        google_api_key_configured=bool(Settings.GOOGLE_API_KEY),
        gemini_model=Settings.GEMINI_MODEL,
    )


@router.get("", response_model=RuntimeSettingsResponse)
async def get_runtime_settings():
    """Get current runtime settings."""
    return _current_settings_response()


@router.post("", response_model=RuntimeSettingsResponse)
async def update_runtime_settings(request: RuntimeSettingsUpdateRequest):
    """Update Gemini runtime settings and persist them to .env."""
    try:
        Settings.update_runtime_config(
            google_api_key=request.google_api_key,
            gemini_model=request.gemini_model,
        )

        from api.routers.verify import verification_service
        from api.routers.evolution import evolution_service

        verification_service._init_components()
        evolution_service.playbook_manager = verification_service.playbook_manager
        evolution_service.reflector = None
        evolution_service.curator = None

        return _current_settings_response()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
