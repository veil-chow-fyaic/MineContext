from pathlib import Path

from cli_anything.minecontext.utils.runtime import inspect_runtime, resolve_minecontext_dir


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
