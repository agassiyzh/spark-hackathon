import json
import tempfile
import unittest
from pathlib import Path

from orchestrator.audit import JsonLineAuditStore
from orchestrator.policy import PolicyEngine
from orchestrator.service import (
    AssistantRequest,
    AssistantService,
    HomeAssistantClientProtocol,
    KnowledgeStoreProtocol,
    LlmClientProtocol,
)


class FakeHomeAssistantClient(HomeAssistantClientProtocol):
    def __init__(self) -> None:
        self.calls = []

    def get_state_snapshot(self):
        return [{"entity_id": "light.living_room", "state": "off", "friendly_name": "Living Room Light"}]

    def get_recent_history(self, entity_ids=None, hours=24):
        return [{"entity_id": "light.living_room", "state": "off", "changed_at": "2026-04-04T12:00:00Z"}]

    def call_service(self, domain, service, entity_id):
        self.calls.append((domain, service, entity_id))
        return {"domain": domain, "service": service, "entity_id": entity_id, "status": "ok"}


class FakeKnowledgeStore(KnowledgeStoreProtocol):
    def get_preferences(self):
        return {"nickname": "Home Assistant"}

    def search(self, query, limit=3):
        return [{"title": "Lighting rules", "content": "Lights may auto-execute if whitelisted."}]


class FakeLlmClient(LlmClientProtocol):
    def complete(self, system_prompt, user_prompt):
        return f"handled:{user_prompt.splitlines()[0]}"


class AssistantServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.audit_store = JsonLineAuditStore(Path(self.tempdir.name) / "audit.jsonl")
        self.service = AssistantService(
            ha_client=FakeHomeAssistantClient(),
            llm_client=FakeLlmClient(),
            knowledge_store=FakeKnowledgeStore(),
            policy_engine=PolicyEngine(auto_execute_entities={"light.living_room"}),
            audit_store=self.audit_store,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_query_request_returns_answer(self) -> None:
        response = self.service.handle_request(
            AssistantRequest(message="What is the living room light status?", request_type="query")
        )

        self.assertEqual(response["status"], "answered")
        self.assertIn("handled:", response["answer"])

    def test_non_whitelisted_control_requires_confirmation(self) -> None:
        response = self.service.handle_request(
            AssistantRequest(
                message="Turn on the heater",
                request_type="control",
                domain="switch",
                service="turn_on",
                entity_id="switch.heater",
                confirmed=False,
            )
        )

        self.assertEqual(response["status"], "confirmation_required")
        self.assertEqual(response["entity_id"], "switch.heater")

    def test_whitelisted_light_control_executes_and_is_audited(self) -> None:
        response = self.service.handle_request(
            AssistantRequest(
                message="Turn on the living room light",
                request_type="control",
                domain="light",
                service="turn_on",
                entity_id="light.living_room",
                confirmed=False,
            )
        )

        self.assertEqual(response["status"], "executed")
        records = self.audit_store.read_recent(limit=5)
        self.assertEqual(records[-1]["status"], "executed")
        self.assertEqual(records[-1]["entity_id"], "light.living_room")


if __name__ == "__main__":
    unittest.main()
