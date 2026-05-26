from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parents[1]
load_dotenv(BACKEND_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Agentic Customer Intelligence API")
    app_env: str = os.getenv("APP_ENV", "development")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    cors_origins: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
    )
    cors_allow_origin_regex: str = os.getenv(
        "CORS_ALLOW_ORIGIN_REGEX",
        r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|172\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)(:\d+)?$",
    )

    openai_api_key: str = os.getenv("OPENAI_API_KEY", os.getenv("LLM_API_KEY", ""))
    openai_base_url: str | None = os.getenv("OPENAI_BASE_URL", os.getenv("LLM_BASE_URL"))
    openai_model: str = os.getenv("OPENAI_MODEL", os.getenv("LLM_MODEL", "gpt-4o-mini"))
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "embed-local")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "700"))

    embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "1536"))

    cluster_profiles_path: Path = Path(
        os.getenv(
            "CLUSTER_PROFILES_PATH",
            str(PROJECT_ROOT / "ml-clustering" / "outputs" / "cluster_profiles.json"),
        )
    )
    knowledge_base_path: Path = Path(
        os.getenv("KNOWLEDGE_BASE_PATH", str(PROJECT_ROOT / "agentic-personas" / "knowledge_base"))
    )
    top_k: int = int(os.getenv("TOP_K", "4"))
    persona_top_k_ratio: float = float(os.getenv("PERSONA_TOP_K_RATIO", "0.67"))
    max_shared_docs: int = int(os.getenv("MAX_SHARED_DOCS", "1"))
    recent_history_turns: int = int(os.getenv("RECENT_HISTORY_TURNS", "2"))

    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "agentic_customer_intelligence")
    postgres_user: str = os.getenv("POSTGRES_USER", "aci")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "aci")
    mongo_host: str = os.getenv("MONGO_HOST", "localhost")
    mongo_port: int = int(os.getenv("MONGO_PORT", "27017"))
    mongo_db: str = os.getenv("MONGO_DB", "agentic_customer_intelligence")
    mongo_collection: str = os.getenv("MONGO_COLLECTION", "conversations")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def postgres_dsn(self) -> str:
        return (
            f"host={self.postgres_host} port={self.postgres_port} dbname={self.postgres_db} "
            f"user={self.postgres_user} password={self.postgres_password}"
        )

    @property
    def mongo_uri(self) -> str:
        return f"mongodb://{self.mongo_host}:{self.mongo_port}"


settings = Settings()
