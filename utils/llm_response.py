"""Helpers for normalizing LLM responses across SDK/model variants."""

from __future__ import annotations

import json
from typing import Any


def _find_json_payload(text: str) -> str:
    """Locate the first valid JSON object/array inside arbitrary text."""
    stripped = text.strip()
    if not stripped:
        return ""

    decoder = json.JSONDecoder()
    for index, char in enumerate(stripped):
        if char not in "{[":
            continue
        try:
            _, end = decoder.raw_decode(stripped[index:])
            return stripped[index:index + end]
        except json.JSONDecodeError:
            continue

    return stripped


def content_to_text(content: Any) -> str:
    """Convert SDK-specific content blocks into plain text."""
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, (int, float, bool)):
        return str(content)

    if isinstance(content, list):
        parts = [content_to_text(item) for item in content]
        return "\n".join(part for part in parts if part)

    if isinstance(content, dict):
        for key in ("text", "output_text", "content", "parts"):
            if key in content:
                return content_to_text(content[key])
        return json.dumps(content, ensure_ascii=False)

    text_attr = getattr(content, "text", None)
    if text_attr is not None and text_attr is not content:
        return content_to_text(text_attr)

    parts_attr = getattr(content, "parts", None)
    if parts_attr is not None and parts_attr is not content:
        return content_to_text(parts_attr)

    content_attr = getattr(content, "content", None)
    if content_attr is not None and content_attr is not content:
        return content_to_text(content_attr)

    return str(content)


def extract_json_text(content: Any) -> str:
    """Extract JSON payload from raw LLM content, with markdown fences stripped."""
    text = content_to_text(content)

    if "```json" in text:
        fenced = text.split("```json", 1)[1].split("```", 1)[0]
        return _find_json_payload(fenced)

    if "```" in text:
        fenced = text.split("```", 1)[1].split("```", 1)[0]
        return _find_json_payload(fenced)

    return _find_json_payload(text)


def preview_content(content: Any, max_length: int = 500) -> str:
    """Return a short printable preview of an LLM response."""
    text = content_to_text(content)
    if len(text) <= max_length:
        return text
    return f"{text[:max_length]}..."
