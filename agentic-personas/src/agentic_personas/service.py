from __future__ import annotations

from .app.agents.graph import build_persona_graph
from .config import load_config
from .llm_client import OpenAICompatibleClient
from .profiles import load_persona_profiles


class PersonaOrchestrator:
    def __init__(self) -> None:
        config = load_config()
        profiles = load_persona_profiles(config.profiles_path)
        llm_client = OpenAICompatibleClient(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key,
            model=config.llm_model,
            temperature=config.llm_temperature,
        )
        self._profiles = profiles
        self._graph = build_persona_graph(profiles=profiles, llm_client=llm_client)

    @property
    def segment_names(self) -> list[str]:
        return [p.segment_name for p in self._profiles]

    def ask(self, question: str) -> dict[str, str]:
        result = self._graph.invoke({"question": question, "responses": {}})
        return result["responses"]
