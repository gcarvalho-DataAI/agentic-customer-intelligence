from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgenticConfig:
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    llm_temperature: float
    profiles_path: Path


def load_config() -> AgenticConfig:
    root = Path(__file__).resolve().parents[3]
    default_profiles_path = root / "ml-clustering" / "outputs" / "cluster_profiles.json"
    return AgenticConfig(
        llm_base_url=os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
        llm_api_key=os.getenv("LLM_API_KEY", "local-key"),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        profiles_path=Path(os.getenv("CLUSTER_PROFILES_PATH", str(default_profiles_path))),
    )

