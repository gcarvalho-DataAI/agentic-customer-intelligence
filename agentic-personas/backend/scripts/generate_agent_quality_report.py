from __future__ import annotations

import argparse
import json
import re
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def post_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def jaccard(a: str, b: str) -> float:
    sa = set(re.findall(r"\w+", normalize(a)))
    sb = set(re.findall(r"\w+", normalize(b)))
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / max(1, len(sa | sb))


def run(base_url: str, output: Path) -> None:
    questions = [
        "Como reagimos a aumento de preço de 10%?",
        "O que faria vocês migrarem para canal digital?",
        "Qual promoção converte melhor para este segmento?",
        "Quais benefícios de fidelidade funcionam melhor?",
    ]
    similarities: list[float] = []
    context_dup_count = 0
    answer_lengths: dict[int, list[int]] = defaultdict(list)

    for question in questions:
        result = post_json(
            f"{base_url}/chat",
            {"question": question, "persona_ids": [0, 1, 2], "include_context": True},
        )
        answers = result["answers"]
        for answer in answers:
            cid = int(answer["cluster_id"])
            answer_lengths[cid].append(len(normalize(answer["answer"])))
            doc_ids = [ctx["doc_id"] for ctx in answer.get("retrieved_context", [])]
            if len(doc_ids) != len(set(doc_ids)):
                context_dup_count += 1
        for i in range(len(answers)):
            for j in range(i + 1, len(answers)):
                similarities.append(jaccard(answers[i]["answer"], answers[j]["answer"]))

    avg_similarity = sum(similarities) / max(1, len(similarities))
    run_at = datetime.now(timezone.utc).isoformat()

    interpretation = []
    if avg_similarity > 0.55:
        interpretation.append("High overlap between personas. Differentiation remains weak.")
    elif avg_similarity > 0.40:
        interpretation.append("Medium overlap. Personas are partially differentiated.")
    else:
        interpretation.append("Low overlap. Good differentiation across personas.")
    if context_dup_count > 0:
        interpretation.append("Some retrieval contexts still repeat in answers.")
    else:
        interpretation.append("No duplicated doc_ids detected in retrieved contexts.")

    lines = [
        "# Agent Quality Report",
        "",
        f"- Generated at: `{run_at}`",
        f"- API base: `{base_url}`",
        "",
        "## Metrics",
        "",
        f"- questions_tested: `{len(questions)}`",
        f"- pairwise_avg_jaccard_similarity: `{avg_similarity:.4f}`",
        f"- context_duplicate_occurrences: `{context_dup_count}`",
    ]
    for cid, lengths in sorted(answer_lengths.items()):
        avg_len = sum(lengths) / max(1, len(lengths))
        lines.append(f"- persona_{cid}_avg_answer_length: `{avg_len:.1f}`")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            *[f"- {item}" for item in interpretation],
            "",
            "## Questions Used",
            "",
            *[f"- {q}" for q in questions],
            "",
        ]
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to: {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8010/api")
    parser.add_argument(
        "--output",
        default="/home/gcarvalho/Documentos/agentic-customer-intelligence/docs/agent_quality_report.md",
    )
    args = parser.parse_args()
    run(args.base_url, Path(args.output))


if __name__ == "__main__":
    main()
