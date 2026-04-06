from __future__ import annotations

import json
from pathlib import Path


class JsonLineAuditStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    def read_recent(self, limit: int = 20) -> list[dict]:
        if not self.path.exists():
            return []

        with self.path.open(encoding="utf-8") as handle:
            lines = handle.readlines()

        return [json.loads(line) for line in lines[-limit:]]
