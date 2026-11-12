import pytest
from fastapi.testclient import TestClient

from app.identifier import IdentificationError, parse_response
from app.main import app, configured_identifier
from app.prompt import build_prompt
from app.schemas import Identification

JPEG = b"\xff\xd8\xff\xe0fake-jpeg-bytes"


class FakeIdentifier:
    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls = result, error, []

    async def identify(self, images, kind="auto", note=""):
        self.calls.append((images, kind, note))
        if self.error:
            raise self.error
        return self.result


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


def use(fake):
    app.dependency_overrides[configured_identifier] = lambda: fake
    return fake


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_serves_web_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Ce copac e ăsta?" in res.text


def test_identify_happy_path(client):
    fake = use(FakeIdentifier(Identification(identificabil=True, nume_popular="Fag")))
    res = client.post(
        "/api/identify",
        files=[("photos", ("a.jpg", JPEG, "image/jpeg"))],
        data={"kind": "frunză", "note": "  parc Cluj  "},
    )
    assert res.status_code == 200
    assert res.json()["nume_popular"] == "Fag"
    images, kind, note = fake.calls[0]
    assert len(images) == 1 and images[0].data == JPEG
    assert (kind, note) == ("frunză", "parc Cluj")


def test_rejects_too_many_photos(client):
    use(FakeIdentifier())
    files = [("photos", (f"{i}.jpg", JPEG, "image/jpeg")) for i in range(5)]
    assert client.post("/api/identify", files=files).status_code == 400


def test_rejects_non_image(client):
    use(FakeIdentifier())
    res = client.post("/api/identify", files=[("photos", ("a.txt", b"hi", "text/plain"))])
    assert res.status_code == 415


def test_rejects_unknown_kind(client):
    use(FakeIdentifier())
    res = client.post(
        "/api/identify",
        files=[("photos", ("a.jpg", JPEG, "image/jpeg"))],
        data={"kind": "rădăcină"},
    )
    assert res.status_code == 400


def test_model_failure_returns_502(client):
    use(FakeIdentifier(error=IdentificationError("indisponibil")))
    res = client.post("/api/identify", files=[("photos", ("a.jpg", JPEG, "image/jpeg"))])
    assert res.status_code == 502
    assert res.json()["detail"] == "indisponibil"


def test_parse_response_handles_fences_and_nulls():
    text = '```json\n{"identificabil": true, "nume_latin": "Fagus sylvatica", "aspect": null, "familie": null}\n```'
    result = parse_response(text)
    assert result.nume_latin == "Fagus sylvatica"
    assert result.familie == ""
    assert result.aspect.scoarta == ""


@pytest.mark.parametrize("text", ["nu e json", '{"nume_popular": "Fag"}', "{stricat"])
def test_parse_response_rejects_bad_output(text):
    with pytest.raises(IdentificationError):
        parse_response(text)


def test_prompt_includes_user_context():
    prompt = build_prompt(2, kind="scoarță", note="Făget, 600 m")
    assert "pozele atașate" in prompt
    assert "scoarță" in prompt and "Făget, 600 m" in prompt
    assert "Utilizatorul spune" not in build_prompt(1)


class _Block:
    def __init__(self, text):
        self.type, self.text = "text", text


class _FakeAnthropic:
    def __init__(self, reply):
        self.reply, self.kwargs = reply, None
        self.messages = self

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return type("Msg", (), {"content": [_Block(self.reply)]})()



def test_tree_identifier_sends_images_and_parses_reply():
    import asyncio

    from app.identifier import Image, TreeIdentifier

    fake = _FakeAnthropic('{"identificabil": true, "nume_popular": "Mesteacăn"}')
    ident = TreeIdentifier(client=fake, model="test-model")
    result = asyncio.run(ident.identify([Image("image/jpeg", JPEG)], "scoarță", ""))

    assert result.nume_popular == "Mesteacăn"
    content = fake.kwargs["messages"][0]["content"]
    assert fake.kwargs["model"] == "test-model"
    assert content[0]["type"] == "image" and content[0]["source"]["media_type"] == "image/jpeg"
    assert "scoarță" in content[-1]["text"]


def test_missing_api_key_returns_503(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    res = client.post("/api/identify", files=[("photos", ("a.jpg", JPEG, "image/jpeg"))])
    assert res.status_code == 503
    assert "ANTHROPIC_API_KEY" in res.json()["detail"]
