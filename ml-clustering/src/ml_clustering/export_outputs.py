from __future__ import annotations

import json
from pathlib import Path
import ast

import pandas as pd

from .profiling import (
    generate_agent_persona_prompt,
    generate_analytical_notes,
    generate_business_interpretation,
)


def export_clustered_consumers(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def export_cluster_summary(summary_df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(output_path, index=False)


def export_cluster_metrics(metrics_df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(output_path, index=False)


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value.strip():
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except (SyntaxError, ValueError):
            return [value]
    return []


def export_cluster_profiles_json(summary_df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    profiles = []
    for _, row in summary_df.iterrows():
        cluster_id = int(row["cluster"])
        differentiators = _as_list(row.get("differentiators", []))
        entry = {
            "cluster_id": cluster_id,
            "segment_name": row["segment_name"],
            "cluster_size": int(row["cluster_size"]),
            "cluster_share": float(row["cluster_share"]),
            "profile": {
                "idade_media": round(float(row["idade_media"]), 2),
                "faixa_etaria_modal": row["faixa_etaria_modal"],
                "ticket_medio_medio": round(float(row["ticket_medio_medio"]), 2),
                "qtd_itens_medio": round(float(row["qtd_itens_medio"]), 2),
                "canal_preferido_modal": row["canal_preferido_modal"],
                "categoria_favorita_modal": row["categoria_favorita_modal"],
                "regiao_modal": row["regiao_modal"],
                "marca_preferida_modal": row["marca_preferida_modal"],
                "influenciador_modal": row["influenciador_modal"],
                "frequencia_compra_modal": row["frequencia_compra_modal"],
                "pagamento_modal": row["pagamento_modal"],
                "genero_modal": row["genero_modal"],
            },
            "differentiators": differentiators,
            "analytical_notes": generate_analytical_notes(row),
            "business_interpretation": generate_business_interpretation(row),
            "persona_prompt": generate_agent_persona_prompt(row),
        }
        profiles.append(entry)

    output_path.write_text(json.dumps(profiles, ensure_ascii=False, indent=2), encoding="utf-8")
