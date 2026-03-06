"""Runtime settings schemas."""

from typing import Optional

from pydantic import BaseModel, Field


class RuntimeSettingsResponse(BaseModel):
    google_api_key_configured: bool
    gemini_model: str
    version: str = "2.0.0"


class RuntimeSettingsUpdateRequest(BaseModel):
    google_api_key: Optional[str] = Field(
        default=None,
        description="Gemini API key. If omitted or empty, the existing key is kept.",
    )
    gemini_model: str = Field(
        default="gemini-3-flash-preview",
        description="Gemini model name to use by default.",
    )
