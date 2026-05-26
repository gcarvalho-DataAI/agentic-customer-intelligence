from __future__ import annotations

import argparse
import json
import re
import urllib.error
import statistics
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


QUESTIONS = [
    "O que faria vocês trocarem de marca na categoria bebidas?",
    "Como vocês reagiriam a um aumento de preço de 10% na categoria bebidas?",
    "Que tipo de promoção teria mais chance de convencer vocês a comprar mais?",
    "O que faria vocês comprarem uma nova marca de bebida pela primeira vez?",
    "Qual benefício seria mais atrativo: desconto imediato, cashback, pontos ou brinde?",
    "O que faria vocês trocarem da loja física para um canal digital?",
    "Que tipo de mensagem chamaria mais atenção antes da compra?",
    "Vocês seriam mais influenciados por preço, conveniência, marca ou recomendação?",
    "O que faria vocês aumentarem a frequência de compra?",
    "Como vocês reagiriam a um combo promocional com bebidas e outros produtos?",
    "O que faria vocês abandonarem uma marca que já compram com frequência?",
    "Qual seria o melhor momento para impactar vocês: antes da compra, dentro da loja ou no checkout?",
    "Que tipo de comunicação parece mais confiável para vocês?",
    "Vocês preferem ofertas personalizadas ou promoções simples para todos?",
    "O que uma marca precisa fazer para virar a escolha recorrente de vocês?",
]

PERSONA_IDS = [0, 1, 2]

FILLERS = [
    "é importante",
    "no entanto",
    "é importante considerar",
    "é importante notar",
    "o que sugere que",
    "pode indicar que",
    "é fundamental considerar",
    "não há evidências fortes",
    "característica da nossa região",
    "diferenciação estatística",
    "lembrar que nossa decisão",
    "lembrar que",
    "nossa decisão tende a ser influenciada",
]

FORBIDDEN_CONSUMER_VOICE_TERMS = [
    "nossas vendas",
    "clientes",
    "fornecedor atual",
    "vendas",
    "nossos consumidores",
    "público-alvo",
    "análise cuidadosa",
    "alta qualidade",
    "disponibilidade garantida",
    "credit-related benefits",
    "nós evitaria",
    "escolha recorrente de nós",
    "marca_",
    "influencer_",
    "impactar nós",
    "para nós seríamos",
    "evitar comunicação pouco clara",
    "ser impactada",
    "isso nos impactar e",
    "isso nos impactar,",
    "a cautela em nossas decisões de compra",
    "a decisões",
    "comprariamos",
    "a conveniência, mas",
    "isso nos faria abandonar a marca",
    "nos faria sentir mais confiança",
    "nos faz sentir mais confiança",
    "podemos se sentir",
    "mais valorizado e incentivado",
    "seja garantida e que",
    "mudanças graduais e sem riscos nos faria",
    "comunicação pouco clara ou que não sejam relevantes",
    "isso nos faz sentir mais conveniência",
    "mais propensos a recomendar a ela",
    "nossa cautela em mudanças graduais",
    "isso nos faria sentir mais confiantes e nos levaria",
    "precisamos ter certeza de que precisamos",
    "isso nos faria evitar nossa cautela",
    "conveniência e pelo controle financeiro",
    "então a marca ofereça",
    "a comunicação seja",
    "a promoção seja",
    "a mudança gradual para nós, então",
    "nós tendemos a preferir se sentir",
    "manter nossa cautela pesa",
    "mais conveniente",
    "motivado a experimentar",
    "preferir pela previsibilidade",
    "benefícios recorrentes e uma transição gradual e de baixo risco de compra também nos faria",
    "a comunicação digital antes da compra para nós",
]

BAD_ENDINGS = (
    " e",
    " de",
    " para",
    " com",
    " sem",
    " a",
    " o",
    " os",
    " as",
    " um",
    " uma",
    " por",
    " que",
    " se",
    " no",
    " na",
    " nos",
    " nas",
    " benef",
    " benefício",
    " benefícios de",
    " migração para",
    " como",
    " pois",
    " em",
    " mud",
    " confian",
    " necess",
    " pre",
)

VERB_LIKE_PATTERN = re.compile(
    r"\b("
    r"é|são|seria|seriam|seríamos|somos|está|estão|ficaria|parece|"
    r"tem|têm|teria|teríamos|precisa|precisamos|pode|podemos|poderia|daria|deixa|"
    r"faz|faria|ajuda|ajudaria|valoriza|valorizamos|preferimos|tendemos|"
    r"buscamos|evitamos|evitaríamos|reagiríamos|compramos|costumamos|"
    r"oferece|ofereçam|garante|mantém|permite|permitiria|influencia|"
    r"impacta|impactaria|leva|levaria|reduz|reduziria|aumenta|aumentaria|"
    r"muda|mudaria|trocaríamos|consideraríamos|conseguiríamos|pesaria|pesa"
    r")\b",
    re.IGNORECASE,
)

PERSONA_MUST = {
    0: {
        "core": ["carteira", "cashback", "desconto", "loja", "confiança", "disponibilidade", "pagamento"],
        "avoid": ["pontos", "cartão de crédito", "digital-first"],
    },
    1: {
        "core": ["crédito", "cartão", "pontos", "digital", "conveniência", "promoção", "antes da compra"],
        "avoid": ["carteira digital", "cashback no caixa"],
    },
    2: {
        "core": [
            "cautela",
            "previsibilidade",
            "previsível",
            "previsíveis",
            "estável",
            "estabilidade",
            "recorrente",
            "gradual",
            "consistência",
            "hábito",
            "rotina",
            "valor",
            "seguro",
            "seguros",
        ],
        "avoid": ["digital-first", "impulsiva", "garantido"],
    },
}

INTENT_KEYWORDS = {
    "brand_switching": ["trocarem de marca", "nova marca", "abandonarem", "escolha recorrente"],
    "price": ["preço", "10%", "desconto imediato", "cashback", "pontos", "brinde"],
    "promotion": ["promoção", "combo", "ofertas"],
    "channel": ["loja física", "canal digital"],
    "communication": ["mensagem", "comunicação", "impactar", "antes da compra", "checkout"],
    "frequency": ["frequência", "comprar mais", "recorrente"],
}


def post_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def words(text: str) -> list[str]:
    return re.findall(r"\w+", normalize(text))


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def jaccard(a: str, b: str) -> float:
    sa = set(words(a))
    sb = set(words(b))
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / max(1, len(sa | sb))


def detect_intents(question: str) -> list[str]:
    q = normalize(question)
    detected = []
    for intent, markers in INTENT_KEYWORDS.items():
        if any(marker in q for marker in markers):
            detected.append(intent)
    return detected or ["general"]


def has_any(text: str, terms: list[str]) -> bool:
    n = normalize(text)
    return any(term in n for term in terms)


def looks_truncated(text: str) -> bool:
    n = normalize(text).rstrip(".!?;:,")
    if not n:
        return False
    if re.fullmatch(r"(como|pois|mas também)", n):
        return True
    if ",." in text:
        return True
    if re.search(r"\b(conveniência e a previsibilidade|lembrar que nossa decisão)\.?$", n):
        return True
    if re.search(r"\b(a decisões|comprariamos|lembrar que|a conveniência,\s*mas|podemos se sentir|mais valorizado e incentivado)\b", n):
        return True
    if re.search(r"\b(nos faria sentir mais confiança|nos faz sentir mais confiança|seja garantida e que|mudanças graduais e sem riscos nos faria|comunicação pouco clara ou que não sejam relevantes|isso nos faz sentir mais conveniência|mais propensos a recomendar a ela|nossa cautela em mudanças graduais|precisamos ter certeza de que precisamos|isso nos faria evitar nossa cautela|conveniência e pelo controle financeiro|então a marca ofereça|a comunicação seja|a promoção seja|a mudança gradual para nós, então|nós tendemos a preferir se sentir|manter nossa cautela pesa|mais conveniente|motivado a experimentar|preferir pela previsibilidade|benefícios recorrentes e uma transição gradual e de baixo risco de compra também nos faria|a conveniência e os benefícios de crédito nos faria)\b", n):
        return True
    if re.search(r"\bisso nos faria sentir mais confiantes\b.*\bnos levaria\b", n):
        return True
    if re.search(r"\ba mudança gradual e a previsibilidade nos faria\b", n):
        return True
    if sum(1 for _ in re.finditer(r"\bisso nos faria\b", n)) > 1:
        return True
    if n.endswith("mudanças significativas em preços"):
        return True
    if n.endswith(BAD_ENDINGS):
        return True
    sentence_parts = sentences(text)
    if sentence_parts:
        last_sentence = normalize(sentence_parts[-1]).rstrip(".!?;:,")
        last_words = words(last_sentence)
        if re.match(r"^evitar\b", last_sentence):
            return True
        if 4 <= len(last_words) <= 8 and not VERB_LIKE_PATTERN.search(last_sentence):
            return True
    if len(sentence_parts) > 1:
        last_words = words(sentence_parts[-1])
        if 0 < len(last_words) < 4:
            return True
    return bool(re.search(r"\b(benef|promo|migração|risco:\s*[ao]?|garantir que os produtos|hes|hesitar|man|necess|mainstream|tende a ser mais|obstá|também|está|poderia|confort|mud|confian|pre|preço está|como|pois)$", n))


def answer_checks(answer: dict[str, Any], question: str) -> dict[str, Any]:
    cid = int(answer["cluster_id"])
    text = answer["answer"]
    n = normalize(text)
    wc = len(words(text))
    sc = len(sentences(text))
    context = answer.get("retrieved_context", [])
    doc_personas = {ctx.get("persona_id") for ctx in context}
    persona_docs = [ctx for ctx in context if ctx.get("persona_id") == f"persona_{cid}"]
    foreign_docs = [
        ctx
        for ctx in context
        if ctx.get("persona_id") not in {f"persona_{cid}", "shared"}
    ]

    filler_hits = [f for f in FILLERS if f in n]
    consumer_voice_hits = [term for term in FORBIDDEN_CONSUMER_VOICE_TERMS if term in n]
    q = normalize(question)
    if int(answer["cluster_id"]) == 0 and "compras online" in n and not any(term in q for term in ["canal digital", "online", "app", "site"]):
        consumer_voice_hits.append("compras online fora de pergunta digital")
    if n.count("isso nos faria") > 1:
        consumer_voice_hits.append("isso nos faria repetido")
    must = PERSONA_MUST[cid]["core"]
    avoid = PERSONA_MUST[cid]["avoid"]
    if cid == 0 and "pontos" in normalize(question):
        avoid = [term for term in avoid if term != "pontos"]
    core_hits = [term for term in must if term in n]
    avoid_hits = [term for term in avoid if term in n]
    is_empty = not text.strip()
    final_sentence_words = len(words(sentences(text)[-1])) if sentences(text) else 0
    short_final_fragment = sc > 1 and 0 < final_sentence_words < 4
    has_truncation = (
        is_empty
        or looks_truncated(text)
        or short_final_fragment
        or (text and text[-1] not in ".!?")
    )

    checks = {
        "word_count": wc,
        "sentence_count": sc,
        "intents": detect_intents(question),
        "filler_hits": filler_hits,
        "consumer_voice_hits": consumer_voice_hits,
        "core_hits": core_hits,
        "avoid_hits": avoid_hits,
        "doc_personas": sorted(str(x) for x in doc_personas if x),
        "persona_doc_count": len(persona_docs),
        "foreign_doc_count": len(foreign_docs),
        "has_truncation": has_truncation,
        "short_final_fragment": short_final_fragment,
        "is_empty": is_empty,
    }

    scores = {
        "concision": 1 if is_empty else 5 if wc <= 90 and 2 <= sc <= 3 else 4 if wc <= 100 and 2 <= sc <= 4 else 2,
        "naturalness": 5 if not filler_hits and not consumer_voice_hits else 3,
        "cluster_fit": 5 if len(core_hits) >= 2 and not avoid_hits else 4 if len(core_hits) >= 1 else 2,
        "rag_grounding": 5 if len(persona_docs) >= 2 and not foreign_docs else 3,
        "guardrails": 5 if not has_truncation and not avoid_hits and not consumer_voice_hits else 3,
    }
    checks["scores"] = scores
    checks["score_avg"] = round(statistics.mean(scores.values()), 2)
    return checks


def score_differentiation(answers: list[dict[str, Any]]) -> tuple[float, list[float]]:
    sims = []
    for i in range(len(answers)):
        for j in range(i + 1, len(answers)):
            sims.append(jaccard(answers[i]["answer"], answers[j]["answer"]))
    avg_sim = statistics.mean(sims) if sims else 0.0
    score = 5 if avg_sim <= 0.32 else 4 if avg_sim <= 0.42 else 3 if avg_sim <= 0.52 else 2
    return float(score), sims


def run(base_url: str, output_json: Path, output_md: Path) -> dict[str, Any]:
    records = []
    question_summaries = []

    for question in QUESTIONS:
        try:
            result = post_json(
                f"{base_url}/chat",
                {"question": question, "persona_ids": PERSONA_IDS, "include_context": True},
            )
        except Exception as exc:
            question_summaries.append(
                {
                    "question": question,
                    "avg_score": 0.0,
                    "differentiation_score": 0.0,
                    "pairwise_similarities": [],
                    "error": str(exc),
                }
            )
            records.append({"question": question, "error": str(exc), "answers": []})
            continue
        answers = result["answers"]
        diff_score, similarities = score_differentiation(answers)
        answer_records = []

        for answer in answers:
            checks = answer_checks(answer, question)
            total_score = round((checks["score_avg"] * 5 + diff_score) / 6, 2)
            answer_records.append(
                {
                    "cluster_id": answer["cluster_id"],
                    "segment_name": answer["segment_name"],
                    "answer": answer["answer"],
                    "checks": checks,
                    "differentiation_score": diff_score,
                    "total_score": total_score,
                    "retrieved_context": [
                        {
                            "doc_id": ctx.get("doc_id"),
                            "persona_id": ctx.get("persona_id"),
                            "doc_type": ctx.get("doc_type"),
                            "confidence": ctx.get("confidence"),
                            "source_file": ctx.get("source_file"),
                            "score": ctx.get("score"),
                        }
                        for ctx in answer.get("retrieved_context", [])
                    ],
                }
            )

        question_avg = round(statistics.mean(r["total_score"] for r in answer_records), 2)
        question_summaries.append(
            {
                "question": question,
                "avg_score": question_avg,
                "differentiation_score": diff_score,
                "pairwise_similarities": [round(s, 3) for s in similarities],
            }
        )
        records.append({"question": question, "answers": answer_records})

    all_scores = [a["total_score"] for r in records for a in r["answers"]]
    failed_questions = [r for r in records if r.get("error")]
    overall = round(statistics.mean(all_scores), 2) if all_scores else 0.0
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "overall_score": overall,
        "target_score": 4.0,
        "failed_question_count": len(failed_questions),
        "passed": bool(all_scores) and not failed_questions and overall >= 4.0 and min(all_scores) >= 3.5,
        "question_summaries": question_summaries,
        "records": records,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(report, output_md)
    return report


def write_markdown_report(report: dict[str, Any], output_md: Path) -> None:
    lines = [
        "# Persona Answer Battery Report",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Overall score: `{report['overall_score']}`",
        f"- Failed questions: `{report.get('failed_question_count', 0)}`",
        f"- Passed: `{report['passed']}`",
        "",
        "## Question Summary",
        "",
    ]
    for item in report["question_summaries"]:
        suffix = f" error=`{item['error']}`" if item.get("error") else ""
        lines.append(f"- `{item['avg_score']}` diff=`{item['differentiation_score']}` | {item['question']}{suffix}")

    lines.extend(["", "## Low Score Answers", ""])
    for record in report["records"]:
        for answer in record["answers"]:
            if answer["total_score"] >= 4.0:
                continue
            checks = answer["checks"]
            lines.extend(
                [
                    f"### Score `{answer['total_score']}` | Persona {answer['cluster_id']} | {record['question']}",
                    "",
                    answer["answer"],
                    "",
                    f"- words: `{checks['word_count']}`",
                    f"- sentences: `{checks['sentence_count']}`",
                    f"- filler_hits: `{checks['filler_hits']}`",
                    f"- consumer_voice_hits: `{checks['consumer_voice_hits']}`",
                    f"- core_hits: `{checks['core_hits']}`",
                    f"- avoid_hits: `{checks['avoid_hits']}`",
                    f"- doc_personas: `{checks['doc_personas']}`",
                    "",
                ]
            )

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8010/api")
    parser.add_argument(
        "--output-json",
        default="/home/gcarvalho/Documentos/agentic-customer-intelligence/agentic-personas/backend/outputs/persona_answer_battery.json",
    )
    parser.add_argument(
        "--output-md",
        default="/home/gcarvalho/Documentos/agentic-customer-intelligence/docs/persona_answer_battery_report.md",
    )
    args = parser.parse_args()
    report = run(args.base_url, Path(args.output_json), Path(args.output_md))
    print(f"overall_score={report['overall_score']}")
    print(f"passed={report['passed']}")
    print(f"json={args.output_json}")
    print(f"markdown={args.output_md}")


if __name__ == "__main__":
    main()
