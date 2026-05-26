from __future__ import annotations

from pathlib import Path
import ast

import pandas as pd

from ml_clustering.paths import OUTPUTS_DIR, PROJECT_ROOT


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


def build_summary_markdown(summary_df: pd.DataFrame, selected_k: int) -> str:
    lines: list[str] = []
    lines.append("# Parte 1 - Resumo Executivo de ML")
    lines.append("")
    lines.append("## Quantidade de clusters")
    lines.append("")
    lines.append(
        f"Foram identificados **{selected_k} segmentos** de consumidores (`k={selected_k}`), "
        "escolhidos com base em métricas internas (silhouette, davies-bouldin, calinski-harabasz), "
        "curva de elbow e interpretabilidade para uso de negócio."
    )
    lines.append("")
    lines.append("## Perfis principais")
    lines.append("")

    for i, row in enumerate(summary_df.sort_values("cluster").itertuples(index=False), start=1):
        differentiators = _as_list(getattr(row, "differentiators", []))
        lines.append(f"1. **{row.segment_name}**")
        lines.append(f"   - Participação: {row.cluster_share * 100:.1f}%")
        lines.append(f"   - Idade média: {row.idade_media:.1f} anos")
        lines.append(f"   - Ticket médio: R$ {row.ticket_medio_medio:.2f}")
        lines.append(
            "   - Traços: "
            f"canal `{row.canal_preferido_modal}`, categoria `{row.categoria_favorita_modal}`, "
            f"frequência `{row.frequencia_compra_modal}` e região `{row.regiao_modal}`."
        )
        if differentiators:
            lines.append(f"   - Diferencial principal: {differentiators[0]}")
        if i < len(summary_df):
            lines.append("")

    lines.append("")
    lines.append("## Aplicações para negócio")
    lines.append("")
    lines.append(
        "1. Ajustar campanhas por faixa etária e região, mantendo linguagem e canal de ativação aderentes ao comportamento de compra."
    )
    lines.append(
        "2. Personalizar ofertas por método de pagamento predominante para elevar conversão sem reduzir margem."
    )
    lines.append(
        "3. Usar os perfis como base de personas sintéticas para simular decisões comerciais (preço, promoções e canais)."
    )
    lines.append("")
    lines.append("## Observações de qualidade analítica")
    lines.append("")
    lines.append(
        "- A base é sintética e tende a concentrar modas categóricas, o que pode reduzir separação semântica entre clusters."
    )
    lines.append(
        "- A segmentação deve ser tratada como base de hipótese e priorização, com validação adicional em contexto real de negócio."
    )
    lines.append(
        "- O cluster mainstream tem menor diferenciação estatística e deve ser apresentado como segmento de transição ou grupo próximo da média da base."
    )
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    summary_path = OUTPUTS_DIR / "cluster_summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(
            f"Missing file: {summary_path}. Run ml-clustering/run_pipeline.py first."
        )

    summary_df = pd.read_csv(summary_path)
    selected_k = int(summary_df["cluster"].nunique())
    markdown = build_summary_markdown(summary_df, selected_k)

    output_path = PROJECT_ROOT / "docs" / "ml-part1-summary.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Summary updated: {output_path}")


if __name__ == "__main__":
    main()
