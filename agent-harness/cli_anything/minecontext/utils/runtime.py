from __future__ import annotations

import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable


def resolve_minecontext_dir(value: str | None = None) -> Path:
    if value:
        return Path(value).expanduser().resolve()

    env_value = os.environ.get("MINECONTEXT_DIR")
    if env_value:
        return Path(env_value).expanduser().resolve()

    cwd = Path.cwd().resolve()
    if (cwd / "opencontext").exists() and (cwd / "frontend").exists():
        return cwd

    return (Path.home() / "Projects" / "MineContext").resolve()


def inspect_runtime(minecontext_dir: Path) -> dict:
    frontend = minecontext_dir / "frontend"
    env_file = minecontext_dir / ".env"
    app_path = resolve_packaged_app_path()
    return {
        "minecontext_dir": str(minecontext_dir),
        "exists": minecontext_dir.exists(),
        "has_opencontext": (minecontext_dir / "opencontext").exists(),
        "has_frontend": frontend.exists(),
        "has_env": env_file.exists(),
        "has_uv": shutil.which("uv") is not None,
        "has_pnpm": shutil.which("pnpm") is not None,
        "packaged_app": str(app_path),
        "has_packaged_app": app_path.exists(),
        "env_file": str(env_file),
        "frontend_dir": str(frontend),
    }


def can_start_dev_runtime(checks: dict) -> bool:
    return all(
        [
            checks["exists"],
            checks["has_opencontext"],
            checks["has_frontend"],
            checks["has_uv"],
            checks["has_pnpm"],
        ]
    )


def resolve_packaged_app_path(value: str | None = None) -> Path:
    if value:
        return Path(value).expanduser().resolve()

    env_value = os.environ.get("MINECONTEXT_APP_PATH")
    if env_value:
        return Path(env_value).expanduser().resolve()

    if platform.system() == "Darwin":
        return Path("/Applications/MineContext.app")

    return Path.home() / "Applications" / "MineContext"


def start_packaged_app(app_path: Path | None = None) -> Path:
    resolved = app_path or resolve_packaged_app_path()
    log_path = log_dir() / "app.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if not resolved.exists():
        raise RuntimeError(f"MineContext packaged app not found: {resolved}")

    if platform.system() == "Darwin":
        with log_path.open("ab") as log_file:
            subprocess.Popen(["open", str(resolved)], stdout=log_file, stderr=subprocess.STDOUT)
        return log_path

    raise RuntimeError("Starting packaged MineContext is currently supported on macOS only")


def start_backend(minecontext_dir: Path, port: int = 1733) -> Path:
    log_path = log_dir() / "backend.log"
    env = load_env_file(minecontext_dir / ".env")
    spawn(["uv", "run", "opencontext", "start", "--port", str(port)], minecontext_dir, log_path, env)
    return log_path


def start_frontend(minecontext_dir: Path) -> Path:
    log_path = log_dir() / "frontend.log"
    env = os.environ.copy()
    env.setdefault("PYTHON", "/usr/bin/python3")
    env.setdefault("npm_config_python", "/usr/bin/python3")
    spawn(["pnpm", "dev"], minecontext_dir / "frontend", log_path, env)
    return log_path


def wait_until(check: Callable[[], bool], timeout: float, interval: float = 0.5) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check():
            return True
        time.sleep(interval)
    return check()


def spawn(command: list[str], cwd: Path, log_path: Path, env: dict[str, str]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("ab")
    subprocess.Popen(
        command,
        cwd=str(cwd),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def load_env_file(path: Path) -> dict[str, str]:
    env = os.environ.copy()
    if not path.exists():
        return env
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            env[key] = value
    return env


def log_dir() -> Path:
    value = os.environ.get("MINECONTEXT_CLI_LOG_DIR")
    if value:
        return Path(value).expanduser().resolve()
    return Path.home() / ".minecontext-cli" / "logs"
