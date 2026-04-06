import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

from orchestrator.audit import JsonLineAuditStore
from orchestrator.policy import PolicyEngine
from orchestrator.server import build_handler, create_server
from orchestrator.service import AssistantService


class FakeHomeAssistantClient:
    def get_state_snapshot(self):
        return []

    def get_recent_history(self, entity_ids=None, hours=24):
        return []

    def call_service(self, domain, service, entity_id):
        return {"domain": domain, "service": service, "entity_id": entity_id, "status": "ok"}


class FakeKnowledgeStore:
    def get_preferences(self):
        return {}

    def search(self, query, limit=3):
        return []


class FakeLlmClient:
    def complete(self, system_prompt, user_prompt):
        return "ok"


class ServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        service = AssistantService(
            ha_client=FakeHomeAssistantClient(),
            llm_client=FakeLlmClient(),
            knowledge_store=FakeKnowledgeStore(),
            policy_engine=PolicyEngine(auto_execute_entities={"light.living_room"}),
            audit_store=JsonLineAuditStore(Path(self.tempdir.name) / "audit.jsonl"),
        )
        handler = build_handler(service)
        self.server = create_server("127.0.0.1", 0, handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.tempdir.cleanup()

    def test_health_endpoint(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.server.server_port)
        conn.request("GET", "/health")
        response = conn.getresponse()
        payload = json.loads(response.read())
        conn.close()

        self.assertEqual(response.status, 200)
        self.assertEqual(payload["status"], "ok")

    def test_assist_endpoint(self) -> None:
        body = json.dumps(
            {
                "message": "Turn on the light",
                "request_type": "control",
                "domain": "light",
                "service": "turn_on",
                "entity_id": "light.living_room",
            }
        )
        conn = HTTPConnection("127.0.0.1", self.server.server_port)
        conn.request("POST", "/assist", body=body, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        payload = json.loads(response.read())
        conn.close()

        self.assertEqual(response.status, 200)
        self.assertEqual(payload["status"], "executed")


if __name__ == "__main__":
    unittest.main()
