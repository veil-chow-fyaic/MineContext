from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class MineContextError(RuntimeError):
    """MineContext harness error."""


@dataclass
class MineContextClient:
    backend_url: str = "http://127.0.0.1:1733"
    control_url: str = "http://127.0.0.1:1734"
    timeout: float = 5.0

    def backend(self, method: str, path: str, body: dict[str, Any] | None = None, params: dict[str, str] | None = None) -> Any:
        return self.request(method, self.backend_url, path, body=body, params=params)

    def control(self, method: str, path: str, body: dict[str, Any] | None = None, params: dict[str, str] | None = None) -> Any:
        return self.request(method, self.control_url, path, body=body, params=params)

    def request(self, method: str, base_url: str, path: str, body: dict[str, Any] | None = None, params: dict[str, str] | None = None) -> Any:
        normalized_path = path if path.startswith("/") else f"/{path}"
        url = f"{base_url.rstrip('/')}{normalized_path}"
        if params:
            url = f"{url}{'&' if '?' in url else '?'}{urlencode(params)}"

        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"

        request = Request(url, data=data, headers=headers, method=method.upper())
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            raise MineContextError(f"{method.upper()} {url} failed: {raw or exc.reason}") from exc
        except (URLError, TimeoutError) as exc:
            raise MineContextError(f"{method.upper()} {url} unavailable: {exc}") from exc

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MineContextError(f"{method.upper()} {url} returned non-JSON") from exc

    def health(self) -> dict[str, Any]:
        backend = self.backend("GET", "/api/health")
        control = self.control("GET", "/health")
        return {"backend": backend, "control": control, "ok": True}

    def recording_status(self) -> Any:
        return self.control("GET", "/recording/status")

    def recording_start(self, config: dict[str, Any] | None = None) -> Any:
        return self.control("POST", "/recording/start", body={"config": config or {}})

    def recording_stop(self) -> Any:
        return self.control("POST", "/recording/stop", body={})

    def model_settings(self) -> Any:
        return self.backend("GET", "/api/model_settings/get")

    def validate_model_settings(self) -> Any:
        settings = self.model_settings()
        config = settings.get("data", {}).get("config", {})
        return self.backend("POST", "/api/model_settings/validate", body={"config": config})

    def update_model_settings(self, config: dict[str, Any]) -> Any:
        return self.backend("POST", "/api/model_settings/update", body={"config": config})
