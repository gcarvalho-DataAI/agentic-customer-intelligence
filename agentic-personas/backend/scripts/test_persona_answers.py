from __future__ import annotations

import json
from typing import Any

import requests


API_URL = "http://127.0.0.1:8010/api/chat"
PERSONA_IDS = [0, 1, 2]
QUESTIONS = [
    "O que faria vocês trocarem de marca na categoria bebidas?",
    "Como vocês reagiriam a um aumento de preço de 10% na categoria bebidas?",
    "O que faria vocês trocarem da loja física para um canal digital?",
    "Que tipo de promoção teria mais chance de convencer vocês a comprar mais?",
]


def ask(question: str) -> dict[str, Any]:
    payload = {
        "question": question,
        "persona_ids": PERSONA_IDS,
        "include_context": True,
    }
    response = requests.post(API_URL, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def print_block(title: str) -> None:
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def main() -> None:
    print_block("Persona Answer Differentiation Test")
    print(f"API URL: {API_URL}")
    print(f"Persona IDs: {PERSONA_IDS}")

    for idx, question in enumerate(QUESTIONS, start=1):
        print_block(f"[{idx}] Pergunta: {question}")
        data = ask(question)
        answers = data.get("answers", [])
        for item in answers:
            segment = item.get("segment_name", "unknown")
            answer = item.get("answer", "").strip()
            context = item.get("retrieved_context", [])
            print(f"\n--- {segment} ---")
            print(answer)
            print("\n[retrieved_context]")
            for c in context:
                preview = (c.get("content", "") or "").replace("\n", " ").strip()
                if len(preview) > 140:
                    preview = preview[:140] + "..."
                print(
                    json.dumps(
                        {
                            "doc_id": c.get("doc_id"),
                            "persona_id": c.get("persona_id"),
                            "doc_type": c.get("doc_type"),
                            "confidence": c.get("confidence"),
                            "source_file": c.get("source_file"),
                            "score": c.get("score"),
                            "content_preview": preview,
                        },
                        ensure_ascii=False,
                    )
                )


if __name__ == "__main__":
    main()
