from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, UTC
from typing import Protocol

from orchestrator.policy import PolicyEngine


class HomeAssistantClientProtocol(Protocol):
    def get_state_snapshot(self): ...
    def get_recent_history(self, entity_ids=None, hours: int = 24): ...
    def call_service(self, domain: str, service: str, entity_id: str): ...


class KnowledgeStoreProtocol(Protocol):
    def get_preferences(self) -> dict: ...
    def search(self, query: str, limit: int = 3) -> list[dict]: ...


class LlmClientProtocol(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str: ...


class AuditStoreProtocol(Protocol):
    def append(self, record: dict) -> None: ...
    def read_recent(self, limit: int = 20) -> list[dict]: ...


@dataclass
class AssistantRequest:
    message: str
    request_type: str
    domain: str | None = None
    service: str | None = None
    entity_id: str | None = None
    confirmed: bool = False


class AssistantService:
    def __init__(
        self,
        ha_client: HomeAssistantClientProtocol,
        llm_client: LlmClientProtocol,
        knowledge_store: KnowledgeStoreProtocol,
        policy_engine: PolicyEngine,
        audit_store: AuditStoreProtocol,
    ) -> None:
        self.ha_client = ha_client
        self.llm_client = llm_client
        self.knowledge_store = knowledge_store
        self.policy_engine = policy_engine
        self.audit_store = audit_store

    def handle_request(self, request: AssistantRequest) -> dict:
        if request.request_type == "control":
            return self._handle_control(request)
        return self._handle_query_or_suggestion(request)

    def _handle_control(self, request: AssistantRequest) -> dict:
        decision = self.policy_engine.evaluate_control(
            domain=request.domain or "",
            entity_id=request.entity_id or "",
            confirmed=request.confirmed,
        )

        if decision.requires_confirmation:
            response = {
                "status": "confirmation_required",
                "reason": decision.reason,
                "entity_id": request.entity_id,
                "domain": request.domain,
                "service": request.service,
            }
            self._audit(request, response)
            return response

        result = self.ha_client.call_service(
            domain=request.domain or "",
            service=request.service or "",
            entity_id=request.entity_id or "",
        )
        response = {
            "status": "executed",
            "entity_id": request.entity_id,
            "domain": request.domain,
            "service": request.service,
            "result": result,
        }
        self._audit(request, response)
        return response

    def _handle_query_or_suggestion(self, request: AssistantRequest) -> dict:
        states = self.ha_client.get_state_snapshot()
        history = self.ha_client.get_recent_history()
        knowledge = self.knowledge_store.search(request.message, limit=3)
        preferences = self.knowledge_store.get_preferences()

        system_prompt = (
            "You are a home assistant orchestrator. Use the provided state, history, "
            "knowledge, and preferences to answer clearly and conservatively."
        )
        user_prompt = "\n".join(
            [
                request.message,
                f"Preferences: {preferences}",
                f"State sample: {states[:5]}",
                f"History sample: {history[:3]}",
                f"Knowledge sample: {knowledge[:3]}",
            ]
        )
        answer = self.llm_client.complete(system_prompt, user_prompt)
        response = {
            "status": "answered",
            "answer": answer,
            "sources": {
                "state_count": len(states),
                "history_count": len(history),
                "knowledge_count": len(knowledge),
            },
        }
        self._audit(request, response)
        return response

    def _audit(self, request: AssistantRequest, response: dict) -> None:
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            **asdict(request),
            **response,
        }
        self.audit_store.append(record)
