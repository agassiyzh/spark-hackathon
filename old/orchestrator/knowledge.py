from __future__ import annotations

import json
from pathlib import Path


class FileKnowledgeStore:
    def __init__(self, knowledge_path: Path, preferences_path: Path) -> None:
        self.knowledge_path = knowledge_path
        self.preferences_path = preferences_path

    def get_preferences(self) -> dict:
        if not self.preferences_path.exists():
            return {}
        return json.loads(self.preferences_path.read_text(encoding="utf-8"))

    def search(self, query: str, limit: int = 3) -> list[dict]:
        if not self.knowledge_path.exists():
            return []

        entries = json.loads(self.knowledge_path.read_text(encoding="utf-8"))
        lowered = query.lower()
        matches = []
        for entry in entries:
            haystack = f"{entry.get('title', '')}\n{entry.get('content', '')}".lower()
            if lowered in haystack:
                matches.append(entry)
        if matches:
            return matches[:limit]
        return entries[:limit]
