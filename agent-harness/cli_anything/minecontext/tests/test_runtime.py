from pathlib import Path

from cli_anything.minecontext.utils.runtime import (
    can_start_dev_runtime,
    inspect_runtime,
    resolve_frontend_dev_command,
    resolve_minecontext_dir,
)


def test_resolve_minecontext_dir_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("MINECONTEXT_DIR", str(tmp_path))
    assert resolve_minecontext_dir() == tmp_path.resolve()


def test_inspect_runtime(tmp_path):
    (tmp_path / "opencontext").mkdir()
    (tmp_path / "frontend").mkdir()
    (tmp_path / ".env").write_text("A=B\n", encoding="utf-8")

    result = inspect_runtime(tmp_path)

    assert result["exists"] is True
    assert result["has_opencontext"] is True
    assert result["has_frontend"] is True
    assert result["has_env"] is True


def test_can_start_dev_runtime_accepts_local_electron_vite_without_pnpm():
    assert can_start_dev_runtime(
        {
            "exists": True,
            "has_opencontext": True,
            "has_frontend": True,
            "has_uv": True,
            "has_pnpm": False,
            "has_npm": False,
            "has_local_electron_vite": True,
        }
    )


def test_resolve_frontend_dev_command_prefers_local_electron_vite(tmp_path):
    local_bin = tmp_path / "frontend" / "node_modules" / ".bin" / "electron-vite"
    local_bin.parent.mkdir(parents=True)
    local_bin.write_text("#!/bin/sh\n", encoding="utf-8")

    assert resolve_frontend_dev_command(tmp_path) == [str(local_bin), "dev"]
