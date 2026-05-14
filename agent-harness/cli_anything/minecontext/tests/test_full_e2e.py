from click.testing import CliRunner

from cli_anything.minecontext import minecontext_cli
from cli_anything.minecontext.minecontext_cli import main


class FakeClient:
    def __init__(self):
        self.calls = []

    def health(self):
        return {"ok": True}

    def recording_status(self):
        return {"success": True, "data": {"status": "running"}}

    def recording_start(self, config=None):
        self.calls.append(("recording_start", config))
        return {"success": True, "config": config}

    def recording_stop(self):
        return {"success": True}

    def model_settings(self):
        return {"success": True}

    def validate_model_settings(self):
        return {"code": 0}

    def update_model_settings(self, config):
        self.calls.append(("update_model_settings", config))
        return {"success": True}

    def backend(self, method, path, body=None, params=None):
        self.calls.append(("backend", method, path, body, params))
        return {"success": True}

    def control(self, method, path, body=None, params=None):
        self.calls.append(("control", method, path, body, params))
        return {"success": True}


def invoke_with_fake(args, fake):
    original = minecontext_cli.MineContextClient
    minecontext_cli.MineContextClient = lambda **kwargs: fake
    try:
        return CliRunner().invoke(main, args)
    finally:
        minecontext_cli.MineContextClient = original


def test_service_health_json():
    result = invoke_with_fake(["--json", "service", "health"], FakeClient())
    assert result.exit_code == 0
    assert '"ok": true' in result.output


def test_recording_start_interval():
    fake = FakeClient()
    result = invoke_with_fake(["--json", "recording", "start", "--interval", "10"], fake)
    assert result.exit_code == 0
    assert fake.calls == [("recording_start", {"recordInterval": 10})]


def test_api_get_passthrough():
    fake = FakeClient()
    result = invoke_with_fake(["--json", "api", "get", "/api/debug/todos", "-p", "limit=2"], fake)
    assert result.exit_code == 0
    assert fake.calls == [("backend", "GET", "/api/debug/todos", None, {"limit": "2"})]


def test_todo_done_semantic_command():
    fake = FakeClient()
    result = invoke_with_fake(["--json", "todo", "done", "7"], fake)
    assert result.exit_code == 0
    assert fake.calls == [("backend", "PATCH", "/api/debug/todos/7", None, {"status": "1"})]


def test_config_set_maps_model_settings():
    fake = FakeClient()
    result = invoke_with_fake(
        [
            "--json",
            "config",
            "set",
            "--provider",
            "doubao",
            "--base-url",
            "https://example.test",
            "--model",
            "vlm",
            "--api-key",
            "key",
            "--embedding-model",
            "emb",
        ],
        fake,
    )

    assert result.exit_code == 0
    assert fake.calls == [
        (
            "update_model_settings",
            {
                "modelPlatform": "doubao",
                "modelId": "vlm",
                "baseUrl": "https://example.test",
                "apiKey": "key",
                "embeddingModelPlatform": "doubao",
                "embeddingModelId": "emb",
                "embeddingBaseUrl": "https://example.test",
                "embeddingApiKey": "key",
            },
        )
    ]


def test_service_up_record_when_services_ready():
    fake = FakeClient()
    result = invoke_with_fake(["--json", "service", "up", "--record", "--wait", "0.1"], fake)

    assert result.exit_code == 0
    assert ("recording_start", {}) in fake.calls
