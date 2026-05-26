from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PersonaProfile:
    cluster_id: int
    segment_name: str
    persona_prompt: str
    business_interpretation: str
    differentiators: list[str]


def load_persona_profiles(path: Path) -> list[PersonaProfile]:
    if not path.exists():
        raise FileNotFoundError(f"Cluster profiles file not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    profiles: list[PersonaProfile] = []
    for row in raw:
        profiles.append(
            PersonaProfile(
                cluster_id=int(row["cluster_id"]),
                segment_name=str(row["segment_name"]),
                persona_prompt=str(row["persona_prompt"]),
                business_interpretation=str(row.get("business_interpretation", "")),
                differentiators=[str(item) for item in row.get("differentiators", [])],
            )
        )
    return profiles
