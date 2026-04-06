from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    allow_execution: bool
    requires_confirmation: bool
    reason: str


class PolicyEngine:
    def __init__(self, auto_execute_entities: set[str] | None = None) -> None:
        self.auto_execute_entities = auto_execute_entities or set()

    def evaluate_control(
        self,
        domain: str,
        entity_id: str,
        confirmed: bool,
    ) -> PolicyDecision:
        if confirmed:
            return PolicyDecision(True, False, "user_confirmed")

        if domain == "light" and entity_id in self.auto_execute_entities:
            return PolicyDecision(True, False, "whitelisted_light")

        return PolicyDecision(False, True, "confirmation_required")
