"""Calls Claude with the photos and turns the answer into an `Identification`."""

import base64
import json
import os
from dataclasses import dataclass
from functools import lru_cache

from anthropic import APIError, AsyncAnthropic
from pydantic import ValidationError

from .prompt import build_prompt
from .schemas import Identification

DEFAULT_MODEL = "claude-sonnet-5-5"


@dataclass(frozen=True)
class Image:
    media_type: str
    data: bytes


class IdentificationError(Exception):
    """The model could not be reached or returned something unusable."""


def parse_response(text: str) -> Identification:
    """Extract the JSON object from the model's text (tolerates ```json fences)."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end < start:
        raise IdentificationError("Răspunsul modelului nu conține JSON.")
    try:
        return Identification.model_validate(json.loads(text[start : end + 1]))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise IdentificationError(
            "Răspunsul modelului nu are formatul așteptat."
        ) from exc


class TreeIdentifier:
    def __init__(self, client: AsyncAnthropic | None = None, model: str | None = None):
        self.client = client or AsyncAnthropic()
        self.model = model or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)

    async def identify(
        self, images: list[Image], kind: str = "auto", note: str = ""
    ) -> Identification:
        content: list[dict] = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img.media_type,
                    "data": base64.b64encode(img.data).decode(),
                },
            }
            for img in images
        ]
        content.append({"type": "text", "text": build_prompt(len(images), kind, note)})

        try:
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                messages=[{"role": "user", "content": content}],
            )
        except APIError as exc:
            raise IdentificationError(
                "Serviciul de identificare nu a răspuns. Încearcă din nou."
            ) from exc

        text = "".join(b.text for b in message.content if b.type == "text")
        return parse_response(text)


@lru_cache
def get_identifier() -> TreeIdentifier:
    return TreeIdentifier()
