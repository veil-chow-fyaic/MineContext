from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Session:
    backend_url: str
    control_url: str
    last_result: Any = None
    history: list[str] = field(default_factory=list)

    def record(self, command: str, result: Any) -> None:
        self.history.append(command)
        self.last_result = result
