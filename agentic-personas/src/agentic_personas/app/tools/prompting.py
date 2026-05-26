from __future__ import annotations

from pathlib import Path

from agentic_personas.profiles import PersonaProfile

PROMPT_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[1] / "agents" / "personas" / "prompts" / "agent.md"
)


def load_agent_prompt_template() -> str:
    return PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8").strip()


def build_persona_system_prompt(profile: PersonaProfile) -> str:
    base_template = load_agent_prompt_template()
    return (
        f"{base_template}\n\n"
        f"Segment Name: {profile.segment_name}\n"
        f"Cluster ID: {profile.cluster_id}\n\n"
        "Segment Prompt Context:\n"
        f"{profile.persona_prompt}\n"
    )
