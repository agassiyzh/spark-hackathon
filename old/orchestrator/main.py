from __future__ import annotations

from orchestrator.audit import JsonLineAuditStore
from orchestrator.config import load_config
from orchestrator.home_assistant import HomeAssistantClient
from orchestrator.knowledge import FileKnowledgeStore
from orchestrator.llm_client import OpenAiCompatibleLlmClient
from orchestrator.policy import PolicyEngine
from orchestrator.server import build_handler, create_server
from orchestrator.service import AssistantService


def main() -> None:
    config = load_config()
    service = AssistantService(
        ha_client=HomeAssistantClient(config.ha_base_url, config.ha_token),
        llm_client=OpenAiCompatibleLlmClient(
            base_url=config.llm_base_url,
            model=config.llm_model,
            api_key=config.llm_api_key,
        ),
        knowledge_store=FileKnowledgeStore(
            knowledge_path=config.knowledge_path,
            preferences_path=config.preferences_path,
        ),
        policy_engine=PolicyEngine(auto_execute_entities=config.auto_execute_entities),
        audit_store=JsonLineAuditStore(config.audit_path),
    )
    server = create_server(config.host, config.port, build_handler(service))
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
