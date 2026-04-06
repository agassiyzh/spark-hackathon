from __future__ import annotations

import json
import urllib.parse
import urllib.request


class HomeAssistantClient:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _request(self, path: str, method: str = "GET", payload: dict | None = None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url=f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def get_state_snapshot(self):
        return self._request("/api/states")

    def get_recent_history(self, entity_ids=None, hours: int = 24):
        params = {"filter_entity_id": ",".join(entity_ids or [])} if entity_ids else {}
        query = urllib.parse.urlencode(params)
        suffix = f"?{query}" if query else ""
        return self._request(f"/api/history/period{suffix}")

    def call_service(self, domain: str, service: str, entity_id: str):
        return self._request(
            f"/api/services/{domain}/{service}",
            method="POST",
            payload={"entity_id": entity_id},
        )
