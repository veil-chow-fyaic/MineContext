from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import click

from cli_anything.minecontext import __version__
from cli_anything.minecontext.core.client import MineContextClient, MineContextError
from cli_anything.minecontext.core.session import Session
from cli_anything.minecontext.utils.runtime import (
    can_start_dev_runtime,
    inspect_runtime,
    resolve_minecontext_dir,
    resolve_packaged_app_path,
    start_backend,
    start_frontend,
    start_packaged_app,
    stop_stale_dev_frontend,
    wait_until,
)

_json_output = False
_repl_mode = False
_client: MineContextClient | None = None
_session: Session | None = None


def get_client() -> MineContextClient:
    if _client is None:
        raise MineContextError("client is not initialized")
    return _client


def output(data: Any, message: str = "") -> None:
    global _session
    if _session is not None:
        _session.last_result = data
    if _json_output:
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
    elif message:
        click.echo(message)
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))


def handle_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MineContextError as exc:
            data = {"success": False, "error": str(exc)}
            if _json_output:
                click.echo(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                click.echo(f"Error: {exc}", err=True)
            if not _repl_mode:
                sys.exit(1)
        except click.ClickException:
            raise
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


@click.group(invoke_without_command=True)
@click.option("--json", "use_json", is_flag=True, help="Output as JSON.")
@click.option("--backend-url", default=None, help="MineContext backend URL.")
@click.option("--control-url", default=None, help="MineContext Electron control API URL.")
@click.option("--timeout", default=60.0, show_default=True, type=float, help="HTTP timeout in seconds.")
@click.version_option(__version__)
@click.pass_context
def main(ctx: click.Context, use_json: bool, backend_url: str | None, control_url: str | None, timeout: float) -> None:
    """MineContext CLI-Anything harness."""
    global _json_output, _client, _session
    _json_output = use_json
    backend = backend_url or os.environ.get("MINECONTEXT_BACKEND_URL", "http://127.0.0.1:1733")
    control = control_url or os.environ.get("MINECONTEXT_CONTROL_URL", "http://127.0.0.1:1734")
    _client = MineContextClient(backend_url=backend, control_url=control, timeout=timeout)
    _session = Session(backend_url=backend, control_url=control)
    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


@main.group()
def service():
    """Service health commands."""


@service.command("health")
@handle_error
def service_health():
    """Check backend and Electron control API health."""
    output(get_client().health())


@service.command("smoke")
@click.option("--date", "summary_date", default="today", help="Daily summary date to verify, or today.")
@click.option("--skip-summary", is_flag=True, help="Skip daily summary lookup.")
@click.option("--skip-chat", is_flag=True, help="Skip Context Agent chat check.")
@click.option("--skip-ui", is_flag=True, help="Skip Electron renderer readiness check.")
@click.option("--require-recording", is_flag=True, help="Fail unless recording is running.")
@handle_error
def service_smoke(summary_date: str, skip_summary: bool, skip_chat: bool, skip_ui: bool, require_recording: bool):
    """Run a distributable end-to-end CLI smoke test."""
    checks: dict[str, Any] = {}
    checks["health"] = probe(lambda: get_client().health())
    checks["model"] = probe(lambda: get_client().validate_model_settings())
    checks["recording"] = probe(lambda: get_client().recording_status())

    if not skip_ui:
        checks["ui"] = probe(assert_ui_ready)

    if not skip_summary:
        checks["summary"] = probe(lambda: assert_daily_report_usable(summary_date))

    if not skip_chat:
        checks["chat"] = probe(
            lambda: get_client().backend("POST", "/api/agent/chat", body={"query": "只回答 cli-smoke-ok"})
        )

    ok = all(check.get("ok") for check in checks.values())
    if require_recording:
        status = checks.get("recording", {}).get("response", {}).get("data", {}).get("status")
        ok = ok and status == "running"

    result = {"ok": ok, "checks": checks}
    output(result)
    if not ok and not _repl_mode:
        raise SystemExit(1)


@service.command("doctor")
@click.option("--minecontext-dir", default=None, type=click.Path(file_okay=False))
@handle_error
def service_doctor(minecontext_dir: str | None):
    """Inspect local MineContext runtime prerequisites."""
    root = resolve_minecontext_dir(minecontext_dir)
    checks = inspect_runtime(root)
    checks["backend_reachable"] = probe(lambda: get_client().backend("GET", "/api/health"))
    checks["control_reachable"] = probe(lambda: get_client().control("GET", "/health"))
    checks["can_start_dev_runtime"] = can_start_dev_runtime(checks)
    checks["can_start_packaged_app"] = checks["has_packaged_app"]
    checks["ok"] = (
        checks["backend_reachable"]["ok"]
        and checks["control_reachable"]["ok"]
        and (checks["can_start_dev_runtime"] or checks["can_start_packaged_app"])
    )
    output(checks)


@service.command("setup")
@click.option("--minecontext-dir", default=None, type=click.Path(file_okay=False))
@handle_error
def service_setup(minecontext_dir: str | None):
    """Resolve and inspect the MineContext runtime location."""
    root = resolve_minecontext_dir(minecontext_dir)
    output(inspect_runtime(root))


@service.command("up")
@click.option("--record", is_flag=True, help="Start recording after services are ready.")
@click.option("--no-ui/--show-ui", default=True, show_default=True, help="Keep Electron running in the background without showing the main window.")
@click.option("--minecontext-dir", default=None, type=click.Path(file_okay=False))
@click.option("--user-data-dir", default=None, type=click.Path(file_okay=False), help="Override Electron userData directory for clean-room validation.")
@click.option("--restart-frontend", is_flag=True, help="Restart the Electron frontend before checking the control API.")
@click.option("--wait", default=45.0, show_default=True, type=float)
@handle_error
def service_up(record: bool, no_ui: bool, minecontext_dir: str | None, user_data_dir: str | None, restart_frontend: bool, wait: float):
    """Start missing MineContext services, optionally start recording."""
    client = get_client()
    root = resolve_minecontext_dir(minecontext_dir)
    checks = inspect_runtime(root)
    app_path = resolve_packaged_app_path()
    resolved_user_data_dir = Path(user_data_dir).expanduser().resolve() if user_data_dir else None
    actions = []
    restarted_frontend = False

    if restart_frontend and can_start_dev_runtime(checks):
        stopped = stop_stale_dev_frontend(root)
        restarted_frontend = True
        if stopped:
            actions.append({"service": "frontend", "action": "stop-stale", "pids": stopped})

    if not probe(lambda: client.backend("GET", "/api/health"))["ok"]:
        if can_start_dev_runtime(checks):
            actions.append({"service": "backend", "action": "start", "log": str(start_backend(root))})
        elif checks["has_packaged_app"]:
            actions.append({"service": "app", "action": "open", "path": str(app_path), "no_ui": no_ui, "user_data_dir": str(resolved_user_data_dir) if resolved_user_data_dir else None, "log": str(start_packaged_app(app_path, no_ui=no_ui, user_data_dir=resolved_user_data_dir))})
        else:
            output({"ok": False, "actions": actions, "error": "no startable MineContext runtime found", "runtime": checks})
            if not _repl_mode:
                raise SystemExit(1)
            return

    if not wait_until(lambda: probe(lambda: client.backend("GET", "/api/health"))["ok"], wait):
        output({"ok": False, "actions": actions, "error": "backend did not become healthy"})
        if not _repl_mode:
            raise SystemExit(1)
        return

    control_ok = probe(lambda: client.control("GET", "/health"))["ok"]
    if restarted_frontend:
        actions.append({"service": "frontend", "action": "start", "no_ui": no_ui, "user_data_dir": str(resolved_user_data_dir) if resolved_user_data_dir else None, "log": str(start_frontend(root, no_ui=no_ui, user_data_dir=resolved_user_data_dir))})
    elif not control_ok:
        if can_start_dev_runtime(checks):
            stopped = stop_stale_dev_frontend(root)
            if stopped:
                actions.append({"service": "frontend", "action": "stop-stale", "pids": stopped})
            actions.append({"service": "frontend", "action": "start", "no_ui": no_ui, "user_data_dir": str(resolved_user_data_dir) if resolved_user_data_dir else None, "log": str(start_frontend(root, no_ui=no_ui, user_data_dir=resolved_user_data_dir))})
        elif checks["has_packaged_app"] and not any(item["service"] == "app" for item in actions):
            actions.append({"service": "app", "action": "open", "path": str(app_path), "no_ui": no_ui, "user_data_dir": str(resolved_user_data_dir) if resolved_user_data_dir else None, "log": str(start_packaged_app(app_path, no_ui=no_ui, user_data_dir=resolved_user_data_dir))})
        elif not checks["has_packaged_app"]:
            output({"ok": False, "actions": actions, "error": "Electron control API is down and no packaged app was found", "runtime": checks})
            if not _repl_mode:
                raise SystemExit(1)
            return

    if not wait_until(lambda: probe(lambda: client.control("GET", "/health"))["ok"], wait):
        output({"ok": False, "actions": actions, "error": "control API did not become healthy"})
        if not _repl_mode:
            raise SystemExit(1)
        return

    recording = client.recording_start({}) if record else None
    output(
        {
            "ok": True,
            "minecontext_dir": str(root),
            "user_data_dir": str(resolved_user_data_dir) if resolved_user_data_dir else None,
            "actions": actions,
            "backend": client.backend("GET", "/api/health"),
            "control": client.control("GET", "/health"),
            "recording": recording,
        }
    )


@main.group()
def recording():
    """Recording control commands."""


@recording.command("status")
@handle_error
def recording_status():
    """Show recording status."""
    output(get_client().recording_status())


@recording.command("start")
@click.option("--config-json", default=None, help="Recording config JSON object.")
@click.option("--interval", type=int, default=None, help="Recording interval in seconds.")
@handle_error
def recording_start(config_json: str | None, interval: int | None):
    """Start recording."""
    config = parse_optional_json(config_json) or {}
    if interval is not None:
        config["recordInterval"] = interval
    output(get_client().recording_start(config))


@recording.command("stop")
@handle_error
def recording_stop():
    """Stop recording."""
    output(get_client().recording_stop())


@main.group()
def window():
    """Electron window visibility commands."""


@window.command("status")
@handle_error
def window_status():
    """Show window visibility status."""
    output(get_client().control("GET", "/window/status"))


@window.command("ui-status")
@handle_error
def window_ui_status():
    """Show Electron renderer readiness status."""
    output(get_client().control("GET", "/ui/status"))


@window.command("show")
@handle_error
def window_show():
    """Show and focus the main window."""
    output(get_client().control("POST", "/window/show"))


@window.command("hide")
@handle_error
def window_hide():
    """Hide the main window without stopping services."""
    output(get_client().control("POST", "/window/hide"))


@main.group()
def config():
    """Model configuration commands."""


@config.command("get")
@handle_error
def config_get():
    """Get model settings."""
    output(get_client().model_settings())


@config.command("validate")
@handle_error
def config_validate():
    """Validate current model settings."""
    output(get_client().validate_model_settings())


@config.command("set")
@click.option("--provider", required=True, help="Model provider, e.g. doubao.")
@click.option("--base-url", required=True, help="VLM base URL.")
@click.option("--model", required=True, help="VLM model ID.")
@click.option("--api-key", required=True, help="VLM API key.")
@click.option("--embedding-provider", default=None, help="Embedding provider. Defaults to --provider.")
@click.option("--embedding-base-url", default=None, help="Embedding base URL. Defaults to --base-url.")
@click.option("--embedding-model", required=True, help="Embedding model ID.")
@click.option("--embedding-api-key", default=None, help="Embedding API key. Defaults to --api-key.")
@handle_error
def config_set(
    provider: str,
    base_url: str,
    model: str,
    api_key: str,
    embedding_provider: str | None,
    embedding_base_url: str | None,
    embedding_model: str,
    embedding_api_key: str | None,
):
    """Validate and save model settings."""
    config = {
        "modelPlatform": provider,
        "modelId": model,
        "baseUrl": base_url,
        "apiKey": api_key,
        "embeddingModelPlatform": embedding_provider or provider,
        "embeddingModelId": embedding_model,
        "embeddingBaseUrl": embedding_base_url or base_url,
        "embeddingApiKey": embedding_api_key or api_key,
    }
    output(get_client().update_model_settings(config))


@main.group()
def chat():
    """Context agent chat commands."""


@chat.command("ask")
@click.argument("query")
@click.option("--session-id", default=None)
@click.option("--context-json", default=None)
@handle_error
def chat_ask(query: str, session_id: str | None, context_json: str | None):
    """Ask MineContext a question."""
    body = {"query": query}
    if session_id:
        body["session_id"] = session_id
    context = parse_optional_json(context_json)
    if context:
        body["context"] = context
    output(get_client().backend("POST", "/api/agent/chat", body=body))


@main.group()
def summary():
    """Daily and weekly summary commands."""


@summary.command("day")
@click.argument("summary_date")
@handle_error
def summary_day(summary_date: str):
    """Read one day's summary by date, e.g. 2026-05-17."""
    output(read_daily_report(summary_date))


@summary.command("audit")
@handle_error
def summary_audit():
    """Audit daily report title/content date consistency."""
    output(audit_daily_reports())


@summary.command("repair-dates")
@click.option("--apply", "apply_changes", is_flag=True, help="Apply the repair plan. Defaults to dry-run.")
@handle_error
def summary_repair_dates(apply_changes: bool):
    """Repair legacy daily report titles so the title date matches the content date."""
    output(repair_daily_report_dates(apply_changes))


@main.group()
def context():
    """Captured context commands."""


@context.command("types")
@handle_error
def context_types():
    """List context types."""
    output(get_client().backend("GET", "/api/context_types"))


@context.command("search")
@click.argument("query")
@click.option("--limit", default=10, show_default=True, type=int)
@click.option("--type", "context_type", default=None)
@handle_error
def context_search(query: str, limit: int, context_type: str | None):
    """Vector search captured context."""
    body = {"query": query, "limit": limit}
    if context_type:
        body["type"] = context_type
    output(get_client().backend("POST", "/api/vector_search", body=body))


@main.group()
def vault():
    """Vault document commands."""


@vault.command("list")
@click.option("--limit", default=50, type=int)
@click.option("--offset", default=0, type=int)
@handle_error
def vault_list(limit: int, offset: int):
    """List vault documents."""
    output(get_client().backend("GET", "/api/vaults/list", params={"limit": str(limit), "offset": str(offset)}))


@vault.command("read")
@click.argument("document_id", type=int)
@handle_error
def vault_read(document_id: int):
    """Read a vault document."""
    output(get_client().backend("GET", f"/api/vaults/{document_id}"))


@vault.command("create")
@click.option("--title", required=True)
@click.option("--content", default=None)
@click.option("--file", "content_file", type=click.Path(exists=True, dir_okay=False), default=None)
@click.option("--type", "document_type", default="note")
@handle_error
def vault_create(title: str, content: str | None, content_file: str | None, document_type: str):
    """Create a vault document."""
    body = {"title": title, "content": read_content(content, content_file), "document_type": document_type}
    output(get_client().backend("POST", "/api/vaults/create", body=body))


@main.group()
def todo():
    """Todo commands."""


@todo.command("list")
@click.option("--status", type=int, default=None)
@click.option("--limit", default=20, type=int)
@click.option("--offset", default=0, type=int)
@handle_error
def todo_list(status: int | None, limit: int, offset: int):
    """List todos."""
    params = {"limit": str(limit), "offset": str(offset)}
    if status is not None:
        params["status"] = str(status)
    output(get_client().backend("GET", "/api/debug/todos", params=params))


@todo.command("done")
@click.argument("todo_id", type=int)
@handle_error
def todo_done(todo_id: int):
    """Mark a todo complete."""
    output(get_client().backend("PATCH", f"/api/debug/todos/{todo_id}", params={"status": "1"}))


@todo.command("generate")
@click.option("--lookback-minutes", default=30, type=int)
@handle_error
def todo_generate(lookback_minutes: int):
    """Generate todos."""
    output(get_client().backend("POST", "/api/debug/generate/todos", params={"lookback_minutes": str(lookback_minutes)}))


@main.group()
def activity():
    """Activity summary commands."""


@activity.command("list")
@click.option("--limit", default=20, type=int)
@click.option("--offset", default=0, type=int)
@handle_error
def activity_list(limit: int, offset: int):
    """List activities."""
    output(get_client().backend("GET", "/api/debug/activities", params={"limit": str(limit), "offset": str(offset)}))


@activity.command("generate")
@click.option("--minutes", default=15, type=int)
@handle_error
def activity_generate(minutes: int):
    """Generate an activity summary."""
    output(get_client().backend("POST", "/api/debug/generate/activity", params={"minutes": str(minutes)}))


@main.group()
def tips():
    """Smart tip commands."""


@tips.command("list")
@click.option("--limit", default=20, type=int)
@click.option("--offset", default=0, type=int)
@handle_error
def tips_list(limit: int, offset: int):
    """List tips."""
    output(get_client().backend("GET", "/api/debug/tips", params={"limit": str(limit), "offset": str(offset)}))


@tips.command("generate")
@click.option("--lookback-minutes", default=60, type=int)
@handle_error
def tips_generate(lookback_minutes: int):
    """Generate a smart tip."""
    output(get_client().backend("POST", "/api/debug/generate/tips", params={"lookback_minutes": str(lookback_minutes)}))


@main.group()
def report():
    """Report commands."""


@report.command("list")
@click.option("--limit", default=20, type=int)
@click.option("--offset", default=0, type=int)
@handle_error
def report_list(limit: int, offset: int):
    """List reports."""
    output(get_client().backend("GET", "/api/debug/reports", params={"limit": str(limit), "offset": str(offset)}))


@report.command("read")
@click.option("--date", "report_date", default=None, help="Daily report date, e.g. 2026-05-17.")
@click.option("--id", "report_id", default=None, type=int, help="Vault document id.")
@handle_error
def report_read(report_date: str | None, report_id: int | None):
    """Read a report by date or document id."""
    if report_id is None and report_date is None:
        raise click.ClickException("use --date YYYY-MM-DD or --id DOCUMENT_ID")
    if report_id is not None and report_date is not None:
        raise click.ClickException("use either --date or --id")
    if report_id is not None:
        output(get_client().backend("GET", f"/api/vaults/{report_id}"))
        return
    output(read_daily_report(report_date or ""))


@report.command("generate")
@click.option("--start-time", type=int, default=None)
@click.option("--end-time", type=int, default=None)
@handle_error
def report_generate(start_time: int | None, end_time: int | None):
    """Generate a report."""
    params = {}
    if start_time is not None:
        params["start_time"] = str(start_time)
    if end_time is not None:
        params["end_time"] = str(end_time)
    output(get_client().backend("POST", "/api/debug/generate/report", params=params))


@main.group()
def monitoring():
    """Monitoring commands."""


@monitoring.command("overview")
@handle_error
def monitoring_overview():
    """Get monitoring overview."""
    output(get_client().backend("GET", "/api/monitoring/overview"))


@monitoring.command("recording-stats")
@handle_error
def monitoring_recording_stats():
    """Get recording stats."""
    output(get_client().backend("GET", "/api/monitoring/recording-stats"))


@main.group()
def api():
    """Backend API passthrough."""


@api.command("get")
@click.argument("path")
@click.option("--param", "-p", multiple=True)
@handle_error
def api_get(path: str, param: tuple[str, ...]):
    """GET backend path."""
    output(get_client().backend("GET", path, params=parse_params(param)))


@api.command("post")
@click.argument("path")
@click.option("--param", "-p", multiple=True)
@click.option("--body-json", default=None)
@handle_error
def api_post(path: str, param: tuple[str, ...], body_json: str | None):
    """POST backend path."""
    output(get_client().backend("POST", path, body=parse_optional_json(body_json), params=parse_params(param)))


@main.group()
def control():
    """Electron control API passthrough."""


@control.command("get")
@click.argument("path")
@click.option("--param", "-p", multiple=True)
@handle_error
def control_get(path: str, param: tuple[str, ...]):
    """GET control path."""
    output(get_client().control("GET", path, params=parse_params(param)))


@control.command("post")
@click.argument("path")
@click.option("--body-json", default=None)
@handle_error
def control_post(path: str, body_json: str | None):
    """POST control path."""
    output(get_client().control("POST", path, body=parse_optional_json(body_json)))


@main.command()
@handle_error
def repl():
    """Start interactive REPL."""
    from cli_anything.minecontext.utils.repl_skin import ReplSkin

    global _repl_mode
    _repl_mode = True
    skin = ReplSkin("minecontext", version=__version__)
    skin.print_banner()
    while True:
        try:
            line = skin.prompt().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in {"quit", "exit"}:
            break
        if line == "help":
            skin.info("Examples: service health | recording status | todo list --status 0 | api get /api/health")
            continue
        args = shlex.split(line)
        try:
            main.main(args=args, standalone_mode=False)
        except SystemExit:
            pass


def parse_optional_json(value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    data = json.loads(value)
    if not isinstance(data, dict):
        raise click.ClickException("JSON value must be an object")
    return data


def parse_params(values: tuple[str, ...]) -> dict[str, str]:
    params = {}
    for value in values:
        if "=" not in value:
            raise click.ClickException(f"invalid parameter '{value}', expected key=value")
        key, val = value.split("=", 1)
        params[key] = val
    return params


def probe(fn) -> dict[str, Any]:
    try:
        return {"ok": True, "response": fn()}
    except MineContextError as exc:
        return {"ok": False, "error": str(exc)}


def assert_ui_ready() -> dict[str, Any]:
    response = get_client().control("GET", "/ui/status")
    data = response.get("data", {}) if isinstance(response, dict) else {}
    if not data.get("ready"):
        raise MineContextError(f"Electron UI is not ready: {data}")
    return response


def read_content(content: str | None, content_file: str | None) -> str:
    if content is not None and content_file is not None:
        raise click.ClickException("use either --content or --file")
    if content_file:
        return Path(content_file).read_text(encoding="utf-8")
    return content or ""


def read_daily_report(raw_date: str) -> dict[str, Any]:
    report_date = normalize_date(raw_date)
    items = list_reports_for_lookup()
    expected_title = f"Daily Report - {report_date}"
    mismatched_reports: list[dict[str, Any]] = []
    mismatched_report_ids: set[Any] = set()

    for item in items:
        if item.get("document_type") == "DailyReport" and item.get("title") == expected_title:
            content_date = extract_daily_report_content_date(str(item.get("content") or ""))
            if content_date and content_date != report_date:
                append_mismatched_report(mismatched_reports, mismatched_report_ids, item, content_date)
                continue
            return {"success": True, "date": report_date, "data": item}

    for item in items:
        title = str(item.get("title") or "")
        if item.get("document_type") == "DailyReport" and report_date in title:
            content_date = extract_daily_report_content_date(str(item.get("content") or ""))
            if content_date and content_date != report_date:
                append_mismatched_report(mismatched_reports, mismatched_report_ids, item, content_date)
                continue
            return {"success": True, "date": report_date, "data": item, "matched_by": "title_contains_date"}

    if mismatched_reports:
        raise MineContextError(
            f"daily report date mismatch for {report_date}; mismatched reports: {mismatched_reports[:20]}"
        )

    available = [
        item.get("title")
        for item in items
        if item.get("document_type") == "DailyReport" and item.get("title")
    ]
    raise MineContextError(f"daily report not found for {report_date}; available reports: {available[:20]}")


def assert_daily_report_usable(raw_date: str) -> dict[str, Any]:
    report = read_daily_report(raw_date)
    content = str(report.get("data", {}).get("content") or "")
    if "No activity data available" not in content:
        return report

    report_date = report["date"]
    activities = get_client().backend(
        "GET",
        "/api/debug/activities",
        params={
            "start_time": f"{report_date}T00:00:00",
            "end_time": f"{report_date}T23:59:59",
            "limit": "1",
            "offset": "0",
        },
    )
    total = activities.get("data", {}).get("total", 0)
    if total:
        raise MineContextError(
            f"daily report for {report_date} is stale: report says no activity, but {total} activity records exist"
        )
    return report


def normalize_date(raw_date: str) -> str:
    if raw_date == "today":
        return date.today().isoformat()
    try:
        return datetime.strptime(raw_date, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise click.ClickException("date must be YYYY-MM-DD or today") from exc


def extract_daily_report_content_date(content: str) -> str | None:
    match = re.search(r"^#\s*日报\s*-\s*(\d{4})年(\d{2})月(\d{2})日\b", content, flags=re.MULTILINE)
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"


def append_mismatched_report(
    mismatched_reports: list[dict[str, Any]],
    seen_ids: set[Any],
    item: dict[str, Any],
    content_date: str,
) -> None:
    report_id = item.get("id")
    if report_id in seen_ids:
        return
    seen_ids.add(report_id)
    mismatched_reports.append({"id": report_id, "title": item.get("title"), "content_date": content_date})


def normalize_daily_report_content(content: str) -> str:
    normalized = content.strip()
    outer_fence = re.match(
        r"^\s*```(?:markdown)?\s*\n([\s\S]*?)\n```\s*$",
        normalized,
        flags=re.IGNORECASE,
    )
    if outer_fence:
        normalized = outer_fence.group(1).strip()
    while re.search(r"\n```[ \t]*$", normalized):
        normalized = re.sub(r"\n```[ \t]*$", "", normalized).strip()
    return normalized


def daily_report_audit_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for item in list_reports_for_lookup():
        if item.get("document_type") != "DailyReport":
            continue
        title = str(item.get("title") or "")
        content = str(item.get("content") or "")
        normalized_content = normalize_daily_report_content(content)
        title_date_match = re.match(r"^Daily Report - (\d{4}-\d{2}-\d{2})$", title)
        title_date = title_date_match.group(1) if title_date_match else None
        content_date = extract_daily_report_content_date(normalized_content)
        no_activity = "No activity data available for the specified time range." in content
        expected_title = f"Daily Report - {content_date}" if content_date else None
        status = "ok"
        if no_activity:
            status = "no_activity"
        elif not content_date:
            status = "missing_content_date"
        elif title_date != content_date:
            status = "mismatch"
        elif normalized_content != content:
            status = "format_artifact"
        entries.append(
            {
                "id": item.get("id"),
                "title": title,
                "title_date": title_date,
                "content_date": content_date,
                "expected_title": expected_title,
                "status": status,
            }
        )
    return entries


def audit_daily_reports() -> dict[str, Any]:
    entries = daily_report_audit_entries()
    issues = [entry for entry in entries if entry["status"] != "ok"]
    return {"success": True, "issues": issues, "total": len(entries), "issue_count": len(issues)}


def repair_daily_report_dates(apply_changes: bool) -> dict[str, Any]:
    reports = [item for item in list_reports_for_lookup() if item.get("document_type") == "DailyReport"]
    reports_by_title = {str(item.get("title") or ""): item for item in reports}
    planned: list[dict[str, Any]] = []

    for item in reports:
        original_content = str(item.get("content") or "")
        content = normalize_daily_report_content(original_content)
        content_date = extract_daily_report_content_date(content)
        if not content_date:
            continue
        expected_title = f"Daily Report - {content_date}"
        current_title = str(item.get("title") or "")
        if current_title != expected_title or content != original_content:
            planned.append(
                {
                    "action": "update",
                    "id": item.get("id"),
                    "from": current_title,
                    "to": expected_title,
                    "content_date": content_date,
                    "normalize_content": content != original_content,
                }
            )

    planned_updates_by_target = {action["to"] for action in planned if action["action"] == "update"}
    for title in planned_updates_by_target:
        existing = reports_by_title.get(title)
        if not existing:
            continue
        content = str(existing.get("content") or "")
        if "No activity data available for the specified time range." in content:
            planned.append({"action": "delete", "id": existing.get("id"), "title": title, "reason": "empty-conflict"})

    if not apply_changes:
        return {"success": True, "dry_run": True, "actions": planned}

    applied: list[dict[str, Any]] = []
    for action in planned:
        if action["action"] == "update":
            item = next(report for report in reports if report.get("id") == action["id"])
            body = {
                "title": action["to"],
                "summary": item.get("summary") or "",
                "content": normalize_daily_report_content(str(item.get("content") or "")),
                "tags": item.get("tags"),
                "document_type": item.get("document_type") or "DailyReport",
            }
            response = get_client().backend("POST", f"/api/vaults/{action['id']}", body=body)
            applied.append({**action, "response": response})
        elif action["action"] == "delete":
            response = get_client().backend("DELETE", f"/api/vaults/{action['id']}")
            applied.append({**action, "response": response})

    return {"success": True, "dry_run": False, "actions": applied}


def list_reports_for_lookup() -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    limit = 100
    offset = 0
    while True:
        response = get_client().backend(
            "GET",
            "/api/debug/reports",
            params={"limit": str(limit), "offset": str(offset)},
        )
        page = response.get("data", {}).get("reports", [])
        if not page:
            break
        reports.extend(page)
        if len(page) < limit:
            break
        offset += limit
    return reports


if __name__ == "__main__":
    main()
