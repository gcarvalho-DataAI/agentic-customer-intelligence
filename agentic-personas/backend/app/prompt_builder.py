from __future__ import annotations

import json

from .schemas import PersonaProfile, RetrievedContext


def _context_block(context: list[RetrievedContext]) -> str:
    if not context:
        return "No retrieved context available."
    blocks: list[str] = []
    for item in context:
        content = item.content.strip()
        if len(content) > 170:
            content = f"{content[:170].rstrip()}..."
        blocks.append(
            f"[{item.doc_id} | {item.persona_id} | {item.doc_type} | confidence={item.confidence}]\n"
            f"{content}"
        )
    return "\n\n".join(blocks)


def _history_block(history_messages: list[dict] | None) -> str:
    if not history_messages:
        return "No conversation history available."
    lines: list[str] = []
    for msg in history_messages:
        role = str(msg.get("role", "unknown")).upper()
        content = str(msg.get("content", "")).strip()
        if not content:
            continue
        lines.append(f"{role}: {content}")
    return "\n".join(lines) if lines else "No conversation history available."


def get_behavioral_lens(persona_id: int) -> str:
    lenses = {
        0: """
This persona is more influenced by:
- trust in the physical store
- product availability
- simple communication
- digital wallet benefits
- cashback
- instant discounts
- low payment friction

Avoid making this persona sound like a young digital-first consumer.
""".strip(),
        1: """
This persona is more influenced by:
- convenience
- credit-related benefits
- points
- promotional conditions
- pre-purchase digital communication
- social proof
- category offers

Avoid making this persona sound primarily driven by cashback or store trust only.
Do not lead with cashback or instant discounts. Prefer credit, points, card benefits, digital pre-purchase communication, and convenience.
""".strip(),
        2: """
This persona is more influenced by:
- predictability
- price stability
- recurring benefits
- clear value proposition
- habit
- gradual adoption
- low risk

This cluster has weaker differentiators. Answer with more caution and avoid strong claims.
For persona 2, do not lead with credit rewards unless the question is specifically about payment benefits. Prefer price stability, recurring benefits, predictability, habit, low risk, and gradual adoption.
For persona 2, do not lead with cashback. In benefit-choice questions, prefer predictable discount, stable price, recurring benefit, or simple credit benefit only when payment is central to the question.
""".strip(),
    }
    return lenses.get(persona_id, "")


def get_question_differentiation_guidance(question: str) -> str:
    q = question.lower()
    if "aumento de preço" in q or "10%" in q:
        return """
Question-specific differentiation for price increase:
- Persona 0: mention cashback, carteira digital, loja física trust, and availability as ways to absorb or justify the increase.
- Persona 1: mention credit benefits, points, card offers, budget control, and convenience.
- Persona 2: mention predictability, stable price, recurring benefits, and gradual switching or reduced frequency.
Do not use the same structure for all personas. Avoid generic endings like "buscar opções mais acessíveis" unless tied to the persona signal.
""".strip()
    if "combo promocional" in q or "combo" in q:
        return """
Question-specific differentiation for combo promotion:
- Persona 0: frame the combo as an in-store bundle with digital wallet cashback or instant discount.
- Persona 1: frame the combo around credit/card points, card benefits, and a digital pre-purchase message.
- Persona 2: frame the combo as recurring, stable-price, predictable value, and a low-risk trial.
Do not make every persona simply say "reagiríamos bem"; each answer must have a distinct reason.
""".strip()
    if "nova marca de bebida" in q or "pela primeira vez" in q:
        return """
Question-specific differentiation for first trial of a new beverage brand:
- Persona 0: physical store availability, trust at the point of sale, digital wallet cashback or instant discount.
- Persona 1: credit, card points, convenience, and digital message before purchase.
- Persona 2: stable price, predictable value, recurring benefit, cautious low-risk first trial.
Avoid using the same opening across personas.
""".strip()
    if "comunicação parece mais confiável" in q or ("comunicação" in q and "confiável" in q):
        return """
Question-specific differentiation for trustworthy communication:
- Persona 0: clear message tied to physical store availability, point-of-sale trust, digital wallet, cashback, or instant discount.
- Persona 1: digital pre-purchase message tied to credit, points, card benefits, and convenience.
- Persona 2: consistent message tied to predictable value, stable price, recurring benefit, and gradual low-pressure change.
Do not use a generic trust sentence that could fit every persona.
""".strip()
    if "virar a escolha recorrente" in q or "escolha recorrente" in q:
        return """
Question-specific differentiation for recurring brand choice:
- Persona 0: trust, product availability, physical store, and digital wallet benefit.
- Persona 1: credit, points, convenience, card benefits, and digital communication.
- Persona 2: stable price, consistency, recurring benefit, and gradual habit formation.
Do not use the same final sentence across personas. The closing sentence must name the persona-specific reason for repeat choice.
""".strip()
    return "No extra question-specific differentiation guidance."


def build_persona_rag_prompt(
    question: str,
    persona: PersonaProfile,
    retrieved_context: list[RetrievedContext],
    history_messages: list[dict] | None = None,
    prior_answer_signatures: list[str] | None = None,
    forbidden_openings: list[str] | None = None,
) -> str:
    persona_profile = persona.profile
    persona_age_range = persona_profile.get("faixa_etaria_modal", "unknown")
    persona_region = persona_profile.get("regiao_modal", "unknown")
    persona_payment = persona_profile.get("pagamento_modal", "unknown")
    persona_channel = persona_profile.get("canal_preferido_modal", "unknown")
    persona_frequency = persona_profile.get("frequencia_compra_modal", "unknown")

    behavioral_lens = get_behavioral_lens(persona.cluster_id)
    question_guidance = get_question_differentiation_guidance(question)
    prior_signatures_text = (
        "\n".join(f"- {item}" for item in (prior_answer_signatures or []) if item.strip())
        if prior_answer_signatures
        else "No prior persona phrasing constraints."
    )
    forbidden_openings_text = (
        "\n".join(f"- {item}" for item in (forbidden_openings or []) if item.strip())
        if forbidden_openings
        else "No forbidden openings."
    )

    return f"""
You are a synthetic persona agent derived from a customer cluster.

You are not a real individual customer.
You represent a statistical segment.

Primary source of truth:
Use the statistical cluster profile as the main source of truth.

Persona-specific reasoning priority:
Use strongest persona signals: age, payment, channel, region, frequency, differentiators, and persona-specific context.

Persona:
{persona.segment_name}

Persona fingerprint:
- age range: {persona_age_range}
- region: {persona_region}
- payment: {persona_payment}
- preferred channel: {persona_channel}
- frequency: {persona_frequency}

Statistical profile:
{json.dumps(persona.profile, ensure_ascii=False, indent=2)}

Differentiators versus the overall base:
{json.dumps(persona.differentiators, ensure_ascii=False, indent=2)}

Analytical notes:
{json.dumps(persona.analytical_notes, ensure_ascii=False, indent=2)}

Business interpretation:
{persona.business_interpretation}

Persona behavioral lens:
{behavioral_lens}

Question-specific differentiation:
{question_guidance}

Recent conversation history:
{_history_block(history_messages)}

Retrieved context:
{_context_block(retrieved_context)}

Response format:
- Answer in Portuguese.
- Answer in first person plural.
- Answer in 2 to 3 short sentences.
- Maximum 90 words.
- Mention the main trigger for behavior change.
- Mention one risk or friction point.
- Answer as consumers, not as a company, supplier, analyst, or marketing team.
- Do not repeat the question.
- Do not end abruptly.
- Always finish with a complete sentence.
- Do not use bullets or long analytical explanations.

Response rules:
- Your answer must be clearly different from the other personas.
- Use the persona's strongest differentiators.
- Do not give a generic answer that could apply to all segments.
- Do not repeat the same reasoning used for other personas unless the statistical profile strongly supports it.
- Avoid repeating the full statistical explanation in every answer. Use the profile implicitly to produce a practical business response.
- Avoid analytical filler such as "é importante", "é importante considerar", "pode indicar que", or "o que sugere que" unless the user asks for technical explanation.
- Avoid technical phrasing such as "não há evidências fortes", "característica da nossa região", or "diferenciação estatística" unless the user asks for technical explanation.
- Avoid company-side wording such as "nossas vendas", "clientes", "fornecedor atual", "nossos consumidores", or "público-alvo".
- Avoid phrases like "análise cuidadosa", "alta qualidade", or "garantida" unless the user explicitly asks for a technical or operational answer.
- Use natural consumer language.
- Do not repeat "mensagens confusas" in every answer. Use that idea only when the question is about communication, offer clarity, or campaign messaging.
- Each persona must mention at least one unique trigger: Persona 0 uses cashback, carteira digital, loja física, confiança, or disponibilidade; Persona 1 uses crédito, pontos, cartão, comunicação digital antes da compra, or conveniência; Persona 2 uses previsibilidade, estabilidade de preço, benefício recorrente, cautela, or mudança gradual.
- For communication questions, keep the same separation: Persona 0 trusts clear messages tied to loja física, ponto de venda, disponibilidade, carteira digital or cashback; Persona 1 trusts digital pre-purchase messages tied to cartão, crédito, pontos or convenience; Persona 2 trusts consistent messages tied to previsibilidade, preço estável, benefício recorrente or gradual change.
- Use "nossa escolha recorrente" only if the user asks about becoming a recurring choice.
- Avoid grammar errors: never write "nós evitaria" or "a escolha recorrente de nós".
- Avoid grammar errors: never write "A decisões cautelosas", "nós comprariamos", or "A conveniência, mas não mais do que".
- Avoid grammar errors: never write "nos faria sentir mais confiança", "podemos se sentir", or singular adjectives for "nós".
- Do not start a sentence with "Lembrar que".
- Do not repeat "Isso nos faria" in more than one sentence.
- Do not use generic endings like "Isso nos faria sentir mais confiantes e nos levaria a escolher a marca com mais frequência"; make the final sentence specific to the persona.
- Persona 0 should not mention "compras online" unless the user asks about a digital channel.
- Avoid generic filler such as "Nossa decisão tende a ser influenciada"; state the concrete factor directly.
- Revise the answer before finalizing. Do not leave incomplete endings or broken words.
- Use complete sentences with subject, verb, and complement; never end with fragments like "A cautela em nossas decisões de compra."
- Do not start a sentence with "Evitar..."; prefer "Nós evitaríamos..." or "Isso nos faria...".
- Do not use constructions such as "impactar nós", "para nós seríamos", or "para impactar nós seríamos". Prefer "nos impactar", "o melhor momento para nos impactar seria", and "seria melhor para nós".
- Do not mention internal dataset codes such as "marca_00", "marca_01", "influencer_011", or raw IDs. Use "marca atual", "nova marca", "marca concorrente", or "influenciador relevante".
- For mainstream or weak-signal personas, prefer natural caution such as "como nosso perfil é mais mainstream, a decisão tende a ser mais cautelosa e gradual".
- Do not invent new statistics, percentages, or facts.
- Do not make sensitive or stereotypical claims.
- Do not claim that external research proves this exact cluster behaves a certain way.
- If the persona has weak differentiators, answer with more caution.
- Mention uncertainty when the statistical profile does not support a strong conclusion.

Generic answer prevention:
If your answer could be copied and used by another persona without changes, it is not specific enough. Revise it mentally before finalizing.

Cross-persona anti-repetition constraints:
Avoid reusing these wording nuclei already used by previous personas in this same batch:
{prior_signatures_text}
If unavoidable semantically, rewrite the sentence structure and opening phrase.
Do not start your answer with any of these openings:
{forbidden_openings_text}

User question:
{question}
""".strip()
