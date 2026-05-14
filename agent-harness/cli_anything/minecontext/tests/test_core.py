import json
from urllib.error import URLError

import pytest

from cli_anything.minecontext.core.client import MineContextClient, MineContextError
from cli_anything.minecontext.core.session import Session


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_client_get_query(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, request.method, request.data))
        return FakeResponse({"ok": True})

    monkeypatch.setattr("cli_anything.minecontext.core.client.urlopen", fake_urlopen)

    client = MineContextClient(backend_url="http://backend")
    result = client.backend("GET", "api/debug/todos", params={"limit": "2"})

    assert result == {"ok": True}
    assert calls == [("http://backend/api/debug/todos?limit=2", "GET", None)]


def test_client_post_body(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, request.method, request.data))
        return FakeResponse(["ok"])

    monkeypatch.setattr("cli_anything.minecontext.core.client.urlopen", fake_urlopen)

    client = MineContextClient(control_url="http://control")
    result = client.control("POST", "/recording/start", body={"config": {"recordInterval": 10}})

    assert result == ["ok"]
    assert calls[0][0] == "http://control/recording/start"
    assert calls[0][1] == "POST"
    assert json.loads(calls[0][2].decode("utf-8")) == {"config": {"recordInterval": 10}}


def test_client_unavailable(monkeypatch):
    def fake_urlopen(request, timeout):
        raise URLError("no service")

    monkeypatch.setattr("cli_anything.minecontext.core.client.urlopen", fake_urlopen)

    with pytest.raises(MineContextError):
        MineContextClient().backend("GET", "/api/health")


def test_session_records_history():
    session = Session("http://backend", "http://control")
    session.record("service health", {"ok": True})
    assert session.history == ["service health"]
    assert session.last_result == {"ok": True}
