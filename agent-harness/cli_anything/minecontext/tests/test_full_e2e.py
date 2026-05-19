from click.testing import CliRunner

from cli_anything.minecontext import minecontext_cli
from cli_anything.minecontext.minecontext_cli import main


class FakeClient:
    def __init__(self):
        self.calls = []

    def health(self):
        return {"ok": True}

    def recording_status(self):
        self.calls.append(("recording_status",))
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
        if path == "/api/model_settings/get":
            return {"data": {"config": {}}}
        if path == "/api/model_settings/validate":
            return {"code": 0, "status": 200}
        if path == "/api/agent/chat":
            return {"success": True, "execution": {"outputs": ["cli-smoke-ok"]}}
        return {"success": True}

    def control(self, method, path, body=None, params=None):
        self.calls.append(("control", method, path, body, params))
        if path == "/recording/status":
            return {"success": True, "data": {"status": "running"}}
        if path == "/ui/status":
            return {"success": True, "data": {"ready": True}}
        return {"success": True}


class FakeReportClient(FakeClient):
    def backend(self, method, path, body=None, params=None):
        if path == "/api/debug/reports":
            self.calls.append(("backend", method, path, body, params))
            return {
                "data": {
                    "reports": [
                        {
                            "id": 5,
                            "title": "Daily Report - 2026-05-17",
                            "content": "daily summary",
                            "document_type": "DailyReport",
                        }
                    ]
                }
            }
        return super().backend(method, path, body=body, params=params)


class FakeStaleReportClient(FakeClient):
    def backend(self, method, path, body=None, params=None):
        if path == "/api/debug/reports":
            self.calls.append(("backend", method, path, body, params))
            return {
                "data": {
                    "reports": [
                        {
                            "id": 6,
                            "title": "Daily Report - 2026-05-18",
                            "content": "No activity data available for the specified time range.",
                            "document_type": "DailyReport",
                        }
                    ]
                }
            }
        if path == "/api/debug/activities":
            self.calls.append(("backend", method, path, body, params))
            return {"data": {"activities": [{"id": 1}], "total": 1}}
        return super().backend(method, path, body=body, params=params)


class FakeMismatchedReportClient(FakeClient):
    def backend(self, method, path, body=None, params=None):
        if path == "/api/debug/reports":
            self.calls.append(("backend", method, path, body, params))
            return {
                "data": {
                    "reports": [
                        {
                            "id": 9,
                            "title": "Daily Report - 2026-05-19",
                            "content": "# 日报 - 2026年05月18日\n\nwrong day",
                            "document_type": "DailyReport",
                        }
                    ]
                }
            }
        return super().backend(method, path, body=body, params=params)


class FakeLegacyShiftedReportsClient(FakeClient):
    def backend(self, method, path, body=None, params=None):
        if path == "/api/debug/reports":
            self.calls.append(("backend", method, path, body, params))
            return {
                "data": {
                    "reports": [
                        {
                            "id": 5,
                            "title": "Daily Report - 2026-05-17",
                            "content": "# 日报 - 2026年05月16日\n\ncontent",
                            "document_type": "DailyReport",
                        },
                        {
                            "id": 4,
                            "title": "Daily Report - 2026-05-16",
                            "content": "# 日报 - 2026年05月15日\n\ncontent",
                            "document_type": "DailyReport",
                        },
                        {
                            "id": 3,
                            "title": "Daily Report - 2026-05-15",
                            "content": "No activity data available for the specified time range.",
                            "document_type": "DailyReport",
                        },
                    ]
                }
            }
        return super().backend(method, path, body=body, params=params)


def invoke_with_fake(args, fake):
    original = minecontext_cli.MineContextClient
    minecontext_cli.MineContextClient = lambda **kwargs: fake
    try:
        return CliRunner().invoke(main, args)
    finally:
        minecontext_cli.MineContextClient = original


def test_default_timeout_is_agent_friendly():
    captured = {}

    def fake_factory(**kwargs):
        captured.update(kwargs)
        return FakeClient()

    original = minecontext_cli.MineContextClient
    minecontext_cli.MineContextClient = fake_factory
    try:
        result = CliRunner().invoke(main, ["--json", "service", "health"])
    finally:
        minecontext_cli.MineContextClient = original

    assert result.exit_code == 0
    assert captured["timeout"] == 60.0


def test_service_health_json():
    result = invoke_with_fake(["--json", "service", "health"], FakeClient())
    assert result.exit_code == 0
    assert '"ok": true' in result.output


def test_service_smoke_skippable_workflow():
    fake = FakeClient()
    result = invoke_with_fake(["--json", "service", "smoke", "--skip-summary", "--skip-chat", "--require-recording"], fake)

    assert result.exit_code == 0
    assert '"ok": true' in result.output
    assert ("recording_status",) in fake.calls


def test_service_smoke_includes_summary_and_chat():
    fake = FakeReportClient()
    result = invoke_with_fake(["--json", "service", "smoke", "--date", "2026-05-17"], fake)

    assert result.exit_code == 0
    assert '"summary"' in result.output
    assert '"chat"' in result.output
    assert '"ui"' in result.output
    assert ("control", "GET", "/ui/status", None, None) in fake.calls
    assert ("backend", "POST", "/api/agent/chat", {"query": "只回答 cli-smoke-ok"}, None) in fake.calls


def test_service_smoke_fails_when_daily_report_is_stale():
    fake = FakeStaleReportClient()
    result = invoke_with_fake(["--json", "service", "smoke", "--date", "2026-05-18", "--skip-chat"], fake)

    assert result.exit_code == 1
    assert "daily report for 2026-05-18 is stale" in result.output


def test_summary_day_fails_when_report_title_and_content_date_mismatch():
    fake = FakeMismatchedReportClient()
    result = invoke_with_fake(["--json", "summary", "day", "2026-05-19"], fake)

    assert result.exit_code == 1
    assert "daily report date mismatch for 2026-05-19" in result.output
    assert "2026-05-18" in result.output


def test_summary_audit_reports_legacy_shifted_dates():
    fake = FakeLegacyShiftedReportsClient()
    result = invoke_with_fake(["--json", "summary", "audit"], fake)

    assert result.exit_code == 0
    assert '"issue_count": 3' in result.output
    assert '"content_date": "2026-05-16"' in result.output


def test_summary_repair_dates_dry_run_plans_updates_and_empty_conflict_delete():
    fake = FakeLegacyShiftedReportsClient()
    result = invoke_with_fake(["--json", "summary", "repair-dates"], fake)

    assert result.exit_code == 0
    assert '"dry_run": true' in result.output
    assert '"action": "update"' in result.output
    assert '"to": "Daily Report - 2026-05-16"' in result.output
    assert '"action": "delete"' in result.output
    assert '"reason": "empty-conflict"' in result.output


def test_service_smoke_fails_when_ui_is_not_ready():
    fake = FakeClient()

    def fake_control(method, path, body=None, params=None):
        fake.calls.append(("control", method, path, body, params))
        if path == "/ui/status":
            return {"success": True, "data": {"ready": False, "renderer": {"textSample": "99%"}}}
        if path == "/recording/status":
            return {"success": True, "data": {"status": "running"}}
        return {"success": True}

    fake.control = fake_control
    result = invoke_with_fake(["--json", "service", "smoke", "--skip-summary", "--skip-chat"], fake)

    assert result.exit_code == 1
    assert '"ui"' in result.output
    assert "Electron UI is not ready" in result.output


def test_service_up_can_restart_frontend_with_clean_user_data(tmp_path, monkeypatch):
    fake = FakeClient()
    started = {}

    monkeypatch.setattr(minecontext_cli, "resolve_minecontext_dir", lambda value=None: tmp_path)
    monkeypatch.setattr(minecontext_cli, "inspect_runtime", lambda root: {"has_packaged_app": False})
    monkeypatch.setattr(minecontext_cli, "can_start_dev_runtime", lambda checks: True)
    monkeypatch.setattr(minecontext_cli, "stop_stale_dev_frontend", lambda root: [123])
    monkeypatch.setattr(minecontext_cli, "wait_until", lambda check, timeout: check())

    def fake_start_frontend(root, no_ui=True, user_data_dir=None):
        started["root"] = root
        started["no_ui"] = no_ui
        started["user_data_dir"] = user_data_dir
        return tmp_path / "frontend.log"

    monkeypatch.setattr(minecontext_cli, "start_frontend", fake_start_frontend)

    user_data_dir = tmp_path / "clean-user-data"
    result = invoke_with_fake(
        [
            "--json",
            "service",
            "up",
            "--restart-frontend",
            "--user-data-dir",
            str(user_data_dir),
        ],
        fake,
    )

    assert result.exit_code == 0
    assert '"action": "stop-stale"' in result.output
    assert '"action": "start"' in result.output
    assert started["user_data_dir"] == user_data_dir


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


def test_window_hide_semantic_command():
    fake = FakeClient()
    result = invoke_with_fake(["--json", "window", "hide"], fake)

    assert result.exit_code == 0
    assert fake.calls == [("control", "POST", "/window/hide", None, None)]


def test_report_read_by_date():
    fake = FakeReportClient()
    result = invoke_with_fake(["--json", "report", "read", "--date", "2026-05-17"], fake)

    assert result.exit_code == 0
    assert '"Daily Report - 2026-05-17"' in result.output
    assert fake.calls == [("backend", "GET", "/api/debug/reports", None, {"limit": "100", "offset": "0"})]


def test_summary_day_alias_reads_daily_report():
    fake = FakeReportClient()
    result = invoke_with_fake(["--json", "summary", "day", "2026-05-17"], fake)

    assert result.exit_code == 0
    assert '"daily summary"' in result.output
