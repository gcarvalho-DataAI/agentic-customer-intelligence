from __future__ import annotations

import ast

import pandas as pd


def _mode_or_unknown(series: pd.Series) -> str:
    mode = series.mode(dropna=True)
    if mode.empty:
        return "desconhecido"
    return str(mode.iloc[0])


def build_cluster_summary(df_with_clusters: pd.DataFrame) -> pd.DataFrame:
    grouped = df_with_clusters.groupby("cluster", dropna=False)
    total = len(df_with_clusters)

    summary = grouped.agg(
        cluster_size=("cluster", "size"),
        idade_media=("idade", "mean"),
        ticket_medio_medio=("ticket_medio", "mean"),
        qtd_itens_medio=("qtd_itens", "mean"),
        canal_preferido_modal=("canal_preferido", _mode_or_unknown),
        categoria_favorita_modal=("categoria_favorita", _mode_or_unknown),
        regiao_modal=("regiao", _mode_or_unknown),
        marca_preferida_modal=("marca_preferida", _mode_or_unknown),
        influenciador_modal=("influenciador", _mode_or_unknown),
        frequencia_compra_modal=("frequencia_compra", _mode_or_unknown),
        pagamento_modal=("pagamento", _mode_or_unknown),
        genero_modal=("genero", _mode_or_unknown),
        faixa_etaria_modal=("faixa_etaria", _mode_or_unknown),
    ).reset_index()

    summary["cluster_share"] = summary["cluster_size"] / total
    return summary


def _ticket_bucket(ticket: float, global_ticket_mean: float) -> str:
    if ticket >= global_ticket_mean * 1.2:
        return "Premium"
    if ticket <= global_ticket_mean * 0.85:
        return "Econômicos"
    return "Ticket Médio"


def assign_segment_names(cluster_summary: pd.DataFrame) -> pd.DataFrame:
    out = cluster_summary.copy()
    names: list[str] = []
    for _, row in out.iterrows():
        idade_media = float(row["idade_media"])
        regiao = str(row["regiao_modal"]).title()
        pagamento = str(row["pagamento_modal"])
        faixa_modal = str(row["faixa_etaria_modal"])

        if idade_media >= 55 and pagamento == "carteira_digital":
            names.append(f"Consumidores Maduros do {regiao} com Pagamento Digital")
            continue

        if idade_media < 35:
            prefix = "Jovens Adultos Recorrentes"
        elif faixa_modal == "55+" and idade_media < 50:
            prefix = "Consumidores Mainstream Recorrentes"
        elif idade_media >= 55:
            prefix = "Consumidores Maduros de Loja Física"
        else:
            prefix = "Consumidores Adultos Recorrentes"

        suffix = f"do {regiao}"
        names.append(f"{prefix} {suffix}")
    out["segment_name"] = names
    return out


def _parse_differentiators(value: object) -> list[str]:
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


def _display_value(value: object) -> str:
    normalized = str(value).replace("_", " ")
    replacements = {
        "loja fisica": "loja física",
        "credito": "crédito",
        "debito": "débito",
    }
    return replacements.get(normalized, normalized)


def _frequency_phrase(value: object) -> str:
    freq = _display_value(value)
    if freq == "semanal":
        return "semanais"
    if freq == "quinzenal":
        return "quinzenais"
    if freq == "mensal":
        return "mensais"
    return freq


def generate_analytical_notes(row: pd.Series) -> list[str]:
    notes: list[str] = []
    idade_media = float(row["idade_media"])
    faixa_modal = str(row["faixa_etaria_modal"])
    if faixa_modal == "55+" and idade_media < 50:
        notes.append(
            "Embora a idade média do cluster seja inferior a 50 anos, a faixa etária modal é 55+, "
            "indicando uma concentração relevante de consumidores mais maduros combinada com "
            "perfis adultos intermediários. Por isso, o segmento foi tratado como mainstream ou "
            "de transição, e não como exclusivamente maduro."
        )

    differentiators = _parse_differentiators(row.get("differentiators", []))
    if "Mainstream" in str(row["segment_name"]) or len(differentiators) <= 1:
        notes.append(
            "Este cluster tem menor diferenciação estatística em relação à base geral. Em uma "
            "evolução do projeto, vale validar K=4, K=5 ou novas estratégias de encoding para "
            "buscar maior separação comportamental."
        )

    return notes


def add_cluster_differentiators(df_with_clusters: pd.DataFrame, cluster_summary: pd.DataFrame) -> pd.DataFrame:
    categorical_cols = [
        "regiao",
        "pagamento",
        "faixa_etaria",
        "canal_preferido",
        "categoria_favorita",
        "frequencia_compra",
    ]
    base_rates = {
        col: df_with_clusters[col].astype(str).value_counts(normalize=True).to_dict()
        for col in categorical_cols
    }
    base_ticket = float(df_with_clusters["ticket_medio"].mean())
    base_items = float(df_with_clusters["qtd_itens"].mean())
    base_age = float(df_with_clusters["idade"].mean())

    rows: list[list[str]] = []
    for _, row in cluster_summary.iterrows():
        cluster_df = df_with_clusters[df_with_clusters["cluster"] == row["cluster"]]
        differentials: list[tuple[float, str]] = []

        for col in categorical_cols:
            top_value = str(cluster_df[col].astype(str).mode(dropna=True).iloc[0])
            cluster_share = float((cluster_df[col].astype(str) == top_value).mean())
            base_share = float(base_rates[col].get(top_value, 0.0))
            lift = cluster_share - base_share
            if lift >= 0.03:
                label = col.replace("_", " ")
                if label == "faixa etaria":
                    label = "faixa etária"
                text = (
                    f"{label} '{_display_value(top_value)}' acima da base "
                    f"({cluster_share:.1%} vs {base_share:.1%})"
                )
                differentials.append((abs(lift), text))

        numeric_checks = [
            ("ticket médio", float(row["ticket_medio_medio"]), base_ticket, "R$"),
            ("quantidade média de itens", float(row["qtd_itens_medio"]), base_items, ""),
            ("idade média", float(row["idade_media"]), base_age, ""),
        ]
        for label, cluster_value, base_value, prefix in numeric_checks:
            if base_value == 0:
                continue
            lift_pct = (cluster_value - base_value) / base_value
            if abs(lift_pct) >= 0.03:
                direction = "acima" if lift_pct > 0 else "abaixo"
                if prefix:
                    text = f"{label} {direction} da base ({prefix} {cluster_value:.2f} vs {prefix} {base_value:.2f})"
                else:
                    text = f"{label} {direction} da base ({cluster_value:.1f} vs {base_value:.1f})"
                differentials.append((abs(lift_pct), text))

        selected = [text for _, text in sorted(differentials, reverse=True)[:5]]
        if not selected:
            selected = [
                "Perfil próximo da média geral da base; diferenças mais úteis aparecem na combinação entre idade, região e pagamento."
            ]
        rows.append(selected)

    out = cluster_summary.copy()
    out["differentiators"] = rows
    return out


def generate_business_interpretation(row: pd.Series) -> str:
    differentiators = _parse_differentiators(row.get("differentiators", []))
    differentiator_text = ""
    if differentiators:
        differentiator_text = " Diferenciais do cluster: " + "; ".join(differentiators[:3]) + "."

    payment = str(row["pagamento_modal"])
    region = str(row["regiao_modal"])
    age = float(row["idade_media"])

    if payment == "carteira_digital":
        payment_behavior = (
            "Como o meio de pagamento dominante é carteira digital, este grupo pode responder bem "
            "a cashback, desconto instantâneo e incentivos financeiros simples."
        )
    else:
        payment_behavior = (
            "Como o pagamento dominante é crédito, este grupo pode responder bem a benefícios de "
            "parcelamento, pontos, limite promocional e ofertas vinculadas ao cartão."
        )

    is_mainstream = "Mainstream" in str(row["segment_name"]) or len(differentiators) <= 1

    if is_mainstream:
        behavior = (
            "Este cluster apresenta menor diferenciação estatística em relação à base geral, "
            "sugerindo um segmento mais mainstream ou de transição entre perfis. Tendem a "
            "valorizar previsibilidade, variedade, estabilidade de preço e benefícios recorrentes, "
            "mas os insights devem ser tratados com mais cautela por dependerem de sinais menos fortes."
        )
    elif age < 35:
        behavior = (
            "Tendem a combinar conveniência com controle financeiro e podem ser ativados por "
            "comunicação digital antes da compra, mesmo mantendo loja física como canal principal."
        )
    elif age >= 55:
        behavior = (
            "Tendem a valorizar confiança no ponto de venda, disponibilidade do produto, "
            "atendimento próximo e comunicação clara sobre benefícios."
        )
    else:
        behavior = (
            "Tendem a valorizar previsibilidade, variedade, estabilidade de preço e benefícios "
            "recorrentes que simplifiquem a decisão de compra."
        )

    analytical_notes = generate_analytical_notes(row)
    analytical_text = ""
    if analytical_notes:
        analytical_text = " Nota analítica: " + " ".join(analytical_notes)

    return (
        f"{row['segment_name']} representa consumidores da região {region}, com compras "
        f"{_frequency_phrase(row['frequencia_compra_modal'])} em "
        f"{_display_value(row['canal_preferido_modal'])}, preferência por "
        f"{_display_value(row['categoria_favorita_modal'])} e ticket médio de "
        f"R$ {row['ticket_medio_medio']:.2f}. "
        f"{behavior} {payment_behavior}{differentiator_text}{analytical_text}"
    )


def generate_agent_persona_prompt(row: pd.Series) -> str:
    interpretation = generate_business_interpretation(row)
    differentiators = _parse_differentiators(row.get("differentiators", []))
    analytical_notes = generate_analytical_notes(row)
    differentiator_block = "\n".join(f"- {item}" for item in differentiators) or "- No strong differentiator detected."
    analytical_block = "\n".join(f"- {item}" for item in analytical_notes) or "- No additional analytical caveat."
    return (
        f'You represent a consumer segment called "{row["segment_name"]}".\n\n'
        "You are not an individual real customer. You are a synthetic persona derived from "
        "statistical patterns of a consumer cluster.\n\n"
        "Segment profile:\n"
        f"- Average age: {row['idade_media']:.1f}\n"
        f"- Dominant age range: {row['faixa_etaria_modal']}\n"
        f"- Preferred channel: {row['canal_preferido_modal']}\n"
        f"- Favorite category: {row['categoria_favorita_modal']}\n"
        f"- Dominant region: {row['regiao_modal']}\n"
        f"- Dominant purchase frequency: {row['frequencia_compra_modal']}\n"
        f"- Dominant payment method: {row['pagamento_modal']}\n"
        f"- Average ticket: R$ {row['ticket_medio_medio']:.2f}\n"
        f"- Average number of items: {row['qtd_itens_medio']:.2f}\n\n"
        "Cluster differentiators versus the overall base:\n"
        f"{differentiator_block}\n\n"
        "Analytical notes:\n"
        f"{analytical_block}\n\n"
        "Behavioral interpretation:\n"
        f"{interpretation}\n\n"
        "Response rules:\n"
        "Answer in first person plural, as a typical group of consumers from this segment.\n"
        "Be consistent with the statistical profile.\n"
        "Do not invent new numbers, percentages, or facts.\n"
        "When asked about price, explain sensitivity qualitatively.\n"
        "When asked about channels, compare the preferred channel with possible alternatives.\n"
        "When asked about promotions, suggest what would be most persuasive for this segment.\n"
        "Keep answers practical and business-oriented.\n"
        "Mention uncertainty when the data does not support a strong conclusion."
    )


def get_top_categories_by_cluster(
    df: pd.DataFrame,
    cluster_col: str,
    categorical_cols: list[str],
    top_n: int = 3,
) -> dict[int, dict[str, list[dict[str, object]]]]:
    output: dict[int, dict[str, list[dict[str, object]]]] = {}
    for cluster_id, gdf in df.groupby(cluster_col):
        output[int(cluster_id)] = {}
        for col in categorical_cols:
            vc = gdf[col].value_counts(dropna=False).head(top_n)
            output[int(cluster_id)][col] = [
                {"value": str(idx), "count": int(count)} for idx, count in vc.items()
            ]
    return output
