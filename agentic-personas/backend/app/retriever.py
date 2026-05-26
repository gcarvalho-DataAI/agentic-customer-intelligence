from __future__ import annotations

import re

from .config import settings
from .llm_client import embed_query
from .schemas import RetrievedContext
from .utils import vector_literal
from .vector_store import COLLECTION_TABLE, get_connection, init_schema


def _detect_intent(question: str) -> set[str]:
    text = question.lower()
    intents: set[str] = set()
    if re.search(r"\b(preço|preco|aumento|desconto|cashback|elasticidade)\b", text):
        intents.add("price")
    if re.search(r"\b(canal|digital|app|online|loja|omnichannel|omnicanal)\b", text):
        intents.add("channel")
    if re.search(r"\b(promo|oferta|cupom|fidelidade|pontos|parcel)\b", text):
        intents.add("promotion")
    if not intents:
        intents.add("general")
    return intents


def _intent_bonus(intents: set[str], item: RetrievedContext) -> float:
    doc = f"{item.doc_type} {item.doc_id}".lower()
    bonus = 0.0
    if "price" in intents and any(k in doc for k in ("price", "cashback", "credit")):
        bonus += 0.08
    if "channel" in intents and any(k in doc for k in ("channel", "digital", "omnichannel", "trust")):
        bonus += 0.08
    if "promotion" in intents and any(k in doc for k in ("promo", "loyalty", "reward", "credit", "payment")):
        bonus += 0.08
    return bonus


def _rerank_by_intent(question: str, items: list[RetrievedContext]) -> list[RetrievedContext]:
    intents = _detect_intent(question)
    return sorted(
        items,
        key=lambda i: (i.score if i.score is not None else 1.0) - _intent_bonus(intents, i),
    )


def _search(question: str, persona_ids: list[str], top_k: int) -> list[RetrievedContext]:
    init_schema()
    embedding = vector_literal(embed_query(question))
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT
                doc_id,
                persona_id,
                doc_type,
                confidence,
                source_file,
                content,
                embedding <=> %(embedding)s::vector AS score
            FROM {COLLECTION_TABLE}
            WHERE persona_id = ANY(%(persona_ids)s)
            ORDER BY embedding <=> %(embedding)s::vector
            LIMIT %(top_k)s
            """,
            {
                "embedding": embedding,
                "persona_ids": persona_ids,
                "top_k": top_k,
            },
        ).fetchall()

    return [
        RetrievedContext(
            doc_id=row[0],
            persona_id=row[1],
            doc_type=row[2],
            confidence=row[3],
            source_file=row[4],
            content=row[5],
            score=float(row[6]) if row[6] is not None else None,
        )
        for row in rows
    ]


def retrieve_context(question: str, persona_id: int, top_k: int | None = None) -> list[RetrievedContext]:
    k = top_k or settings.top_k
    persona_key = f"persona_{persona_id}"
    # Default strategy for side-by-side persona comparison:
    # 2 persona-specific + 1 shared behavioral + 1 shared guardrail.
    persona_k = min(2, max(1, k))
    shared_behavioral_k = 1 if k >= 3 else 0
    shared_guardrail_k = 1 if k >= 4 else 0

    persona_results = _rerank_by_intent(question, _search(question, [persona_key], max(persona_k * 3, 3)))
    intents = _detect_intent(question)
    shared_pool = _rerank_by_intent(question, _search(question, ["shared"], 12))
    shared_behavioral_results = [i for i in shared_pool if i.doc_type != "guardrails"]
    shared_guardrail_results = [i for i in shared_pool if i.doc_type == "guardrails"]

    # Intent-focused shared context to reduce cross-persona generic drift.
    if "channel" in intents:
        shared_behavioral_results = [
            i for i in shared_behavioral_results if i.doc_type in ("omnichannel", "behavioral_science")
        ]
    elif "price" in intents:
        shared_behavioral_results = [
            i for i in shared_behavioral_results if i.doc_type in ("price_sensitivity", "behavioral_science")
        ]
    elif "promotion" in intents:
        shared_behavioral_results = [
            i for i in shared_behavioral_results if i.doc_type in ("behavioral_science", "price_sensitivity")
        ]
    else:
        shared_behavioral_results = [
            i for i in shared_behavioral_results if i.doc_type in ("behavioral_science", "omnichannel")
        ]

    combined: list[RetrievedContext] = []
    seen_doc_ids: set[str] = set()

    persona_added = 0
    for item in persona_results:
        if item.doc_id in seen_doc_ids:
            continue
        if persona_added >= persona_k:
            break
        seen_doc_ids.add(item.doc_id)
        combined.append(item)
        persona_added += 1

    shared_behavioral_added = 0
    for item in shared_behavioral_results:
        if item.doc_id in seen_doc_ids:
            continue
        if shared_behavioral_added >= shared_behavioral_k:
            break
        seen_doc_ids.add(item.doc_id)
        combined.append(item)
        shared_behavioral_added += 1

    shared_guardrail_added = 0
    for item in shared_guardrail_results:
        if item.doc_id in seen_doc_ids:
            continue
        if shared_guardrail_added >= shared_guardrail_k:
            break
        seen_doc_ids.add(item.doc_id)
        combined.append(item)
        shared_guardrail_added += 1

    for item in [*persona_results, *shared_behavioral_results, *shared_guardrail_results]:
        if len(combined) >= k:
            break
        key = item.doc_id
        if key in seen_doc_ids:
            continue
        seen_doc_ids.add(key)
        combined.append(item)
    return combined[:k]
