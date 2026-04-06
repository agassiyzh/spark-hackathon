from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from orchestrator.service import AssistantRequest, AssistantService


def build_handler(service: AssistantService):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self._send_json(200, {"status": "ok"})
                return
            if self.path.startswith("/audit"):
                self._send_json(200, {"records": service.audit_store.read_recent(limit=20)})
                return
            self._send_json(404, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/assist":
                self._send_json(404, {"error": "not_found"})
                return

            payload = self._read_json()
            request = AssistantRequest(
                message=payload["message"],
                request_type=payload["request_type"],
                domain=payload.get("domain"),
                service=payload.get("service"),
                entity_id=payload.get("entity_id"),
                confirmed=payload.get("confirmed", False),
            )
            response = service.handle_request(request)
            self._send_json(200, response)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def _read_json(self) -> dict:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            return json.loads(body.decode("utf-8"))

        def _send_json(self, status: int, payload: dict) -> None:
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return Handler


def create_server(host: str, port: int, handler) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), handler)
