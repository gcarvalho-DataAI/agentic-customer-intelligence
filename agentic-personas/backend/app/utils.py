from __future__ import annotations

import re


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"

