# Ce copac e ăsta? 🌳

Upload a photo of a leaf, needles or bark and get back which tree it is, plus a
field guide entry: how to recognise it, where it grows (with a focus on Romania)
and what its fruit, leaves, bark and wood are used for.

The UI is in Romanian; the code and docs are in English.

## How it works

```
browser ──(multipart: 1–4 photos, kind, note)──▶ FastAPI /api/identify
                                                   │ validates type / size / count
                                                   ▼
                                           Claude (vision) via Anthropic API
                                                   │ strict JSON answer
                                                   ▼
                                    Pydantic model ─▶ JSON ─▶ rendered field guide
```

- **`app/main.py`**: FastAPI app. Validates uploads (max 4 photos, 5 MB each,
  image types only) and serves the static front end.
- **`app/identifier.py`**: sends the photos to Claude, extracts the JSON from
  the reply and maps API/parsing failures to a single `IdentificationError`
  (returned as HTTP 502).
- **`app/schemas.py`**: lenient Pydantic models. Unknown keys are ignored and
  `null` falls back to defaults, so small deviations in the model's output
  don't break the UI.
- **`app/prompt.py`**: the prompt, including the JSON contract and rules about
  being honest with confidence and listing look-alike species.
- **`static/index.html`**: a single page in vanilla JS. Photos are resized in
  the browser (max 1400 px) before upload to keep requests small.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # then put your Anthropic API key in .env
uvicorn app.main:app --reload
```

Open http://localhost:8000.

You need an API key from https://console.anthropic.com. Each identification is
one request with images, so it costs a few cents.

## Tests

```bash
pytest
```

The tests replace the Claude client with a fake through FastAPI dependency
overrides, so they run offline and need no API key.

## Docker

```bash
docker build -t ce-copac .
docker run -p 8000:8000 --env-file .env ce-copac
```

## Ideas for next steps

- Save the history of identifications (SQLite / Postgres) and add a
  "my trees" page
- Rate limiting per IP
- Cache results by image hash
- Deploy (Render, Fly.io, Railway)

## Disclaimer

Identification from photos can be wrong. Don't eat fruit or use plant parts as
remedies based on this app alone.
