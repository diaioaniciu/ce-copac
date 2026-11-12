"""FastAPI app: serves the web page and the /api/identify endpoint."""

import os
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from .identifier import IdentificationError, Image, TreeIdentifier, get_identifier
from .schemas import Identification

load_dotenv()

MAX_FILES = 4
MAX_BYTES = 5 * 1024 * 1024  # 5 MB per photo
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
KINDS = {"auto", "frunză", "ace / conuri", "scoarță"}
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Ce copac e ăsta?")


def configured_identifier() -> TreeIdentifier:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(
            503, "Serverul nu are cheie API. Pune ANTHROPIC_API_KEY în fișierul .env."
        )
    return get_identifier()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/identify", response_model=Identification)
async def identify(
    photos: Annotated[list[UploadFile], File()],
    kind: Annotated[str, Form()] = "auto",
    note: Annotated[str, Form(max_length=300)] = "",
    identifier: TreeIdentifier = Depends(configured_identifier),
) -> Identification:
    if not 1 <= len(photos) <= MAX_FILES:
        raise HTTPException(400, f"Trimite între 1 și {MAX_FILES} poze.")
    if kind not in KINDS:
        raise HTTPException(400, "Tip de poză necunoscut.")

    images: list[Image] = []
    for photo in photos:
        if photo.content_type not in ALLOWED_TYPES:
            raise HTTPException(415, "Acceptăm doar poze JPEG, PNG, WebP sau GIF.")
        data = await photo.read()
        if len(data) > MAX_BYTES:
            raise HTTPException(413, "Fiecare poză poate avea maximum 5 MB.")
        images.append(Image(media_type=photo.content_type, data=data))

    try:
        return await identifier.identify(images, kind, note.strip())
    except IdentificationError as exc:
        raise HTTPException(502, str(exc)) from exc


# Mounted last so the API routes above take precedence.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
