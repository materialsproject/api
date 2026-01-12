"""Define auxiliary schemas used by some LLMs."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from mp_api.client.core.utils import validate_ids


class OpenAIResult(BaseModel):
    """Schematize result for OpenAI support."""

    id: str
    title: str | None = None
    text: str | None = None
    url: str | None = None
    metadata: dict[str, str] | None = None

    @model_validator(mode="before")
    def set_url(cls, config: Any) -> Any:
        """Set default Materials Project URL and title."""
        formatted_mpid = validate_ids([config.get("id")])[0]
        if not config.get("title"):
            config["title"] = formatted_mpid

        if not config.get("url"):
            config["url"] = (
                "https://next-gen.materialsproject.org/materials/" f"{formatted_mpid}"
            )
        return config


class OpenAISearchOutput(BaseModel):
    """Schematize data for OpenAI support."""

    results: list[OpenAIResult] = Field([])
