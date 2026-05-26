from __future__ import annotations

import json
from functools import lru_cache

from .config import settings
from .schemas import PersonaProfile


REQUIRED_FIELDS = {
    "cluster_id",
    "segment_name",
    "cluster_size",
    "cluster_share",
    "profile",
    "differentiators",
    "business_interpretation",
    "persona_prompt",
}


@lru_cache(maxsize=1)
def load_personas() -> list[PersonaProfile]:
    path = settings.cluster_profiles_path
    if not path.exists():
        raise FileNotFoundError(f"Cluster profiles file not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    seen_ids: set[int] = set()
    personas: list[PersonaProfile] = []
    for item in raw:
        missing = REQUIRED_FIELDS.difference(item)
        if missing:
            raise ValueError(f"Persona profile is missing fields {sorted(missing)}")
        cluster_id = int(item["cluster_id"])
        if cluster_id in seen_ids:
            raise ValueError(f"Duplicated cluster_id in profiles: {cluster_id}")
        seen_ids.add(cluster_id)
        personas.append(PersonaProfile.model_validate(item))
    return personas


def get_persona_by_id(cluster_id: int) -> PersonaProfile:
    for persona in load_personas():
        if persona.cluster_id == cluster_id:
            return persona
    raise KeyError(f"Persona not found: {cluster_id}")

