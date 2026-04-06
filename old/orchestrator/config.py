from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    host: str
    port: int
    llm_base_url: str
    llm_model: str
    llm_api_key: str
    ha_base_url: str
    ha_token: str
    auto_execute_entities: set[str]
    knowledge_path: Path
    preferences_path: Path
    audit_path: Path


def load_config() -> AppConfig:
    data_dir = Path(os.getenv("ORCH_DATA_DIR", "./data/orchestrator"))
    auto_execute_entities = {
        entity.strip()
        for entity in os.getenv("AUTO_EXECUTE_ENTITIES", "light.living_room").split(",")
        if entity.strip()
    }
    return AppConfig(
        host=os.getenv("ORCH_HOST", "0.0.0.0"),
        port=int(os.getenv("ORCH_PORT", "8081")),
        llm_base_url=os.getenv("LLM_BASE_URL", "http://llm-brain:8000/v1"),
        llm_model=os.getenv("LLM_MODEL", os.getenv("HF_MODEL_HANDLE", "local-model")),
        llm_api_key=os.getenv("LLM_API_KEY", "sk-local-dummy-key"),
        ha_base_url=os.getenv("HA_BASE_URL", "http://host.docker.internal:8123"),
        ha_token=os.getenv("HA_TOKEN", ""),
        auto_execute_entities=auto_execute_entities,
        knowledge_path=data_dir / "knowledge.json",
        preferences_path=data_dir / "preferences.json",
        audit_path=data_dir / "audit.jsonl",
    )
