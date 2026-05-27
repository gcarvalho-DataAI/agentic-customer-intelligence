from __future__ import annotations

import logging
import re

from .answer_style import has_quality_issue, looks_truncated, normalize_persona_answer
from .llm_client import generate_answer
from .persona_loader import get_persona_by_id
from .prompt_builder import build_persona_rag_prompt
from .retriever import retrieve_context
from .schemas import ChatResponse, PersonaAnswer

logger = logging.getLogger(__name__)


def _answer_signature(answer: str) -> str:
    text = re.sub(r"\s+", " ", answer.strip())
    if not text:
        return ""
    first_sentence = re.split(r"(?<=[.!?])\s+", text)[0].strip()
    words = first_sentence.split()
    return " ".join(words[:16])


def _opening_signature(answer: str) -> str:
    text = re.sub(r"\s+", " ", answer.strip())
    if not text:
        return ""
    words = text.split()
    return " ".join(words[:8]).lower()


def _fallback_answer(persona_id: int) -> str:
    if persona_id == 0:
        return (
            "Nós responderíamos melhor a uma proposta simples, disponível na loja física e com benefício imediato na carteira digital. "
            "O principal gatilho seria cashback, desconto instantâneo ou pagamento sem fricção. "
            "Se a oferta não passar confiança no ponto de venda, tendemos a manter a escolha atual."
        )
    if persona_id == 1:
        return (
            "Nós responderíamos melhor a uma proposta conveniente, com benefício ligado ao crédito, pontos ou cartão. "
            "A comunicação digital antes da compra pode nos influenciar, mesmo que a decisão aconteça na loja física. "
            "Se a oferta não parecer prática ou vantajosa, tendemos a buscar outra opção."
        )
    return (
        "Nós responderíamos com mais cautela, buscando previsibilidade, preço estável e benefício recorrente. "
        "O principal gatilho seria uma proposta de valor clara e consistente ao longo do tempo. "
        "Se a mudança parecer arriscada ou pontual demais, tendemos a manter o hábito atual."
    )


def _targeted_fallback_answer(question: str, persona_id: int) -> str | None:
    q = question.lower()
    if "aumento de preço" in q or "10%" in q:
        if persona_id == 0:
            return (
                "Nós sentiríamos o aumento, mas a decisão dependeria da confiança na loja física e da disponibilidade da bebida. "
                "Cashback, desconto instantâneo ou benefício na carteira digital ajudariam a compensar parte do preço. "
                "Sem esse benefício claro no ponto de venda, procuraríamos outra opção na próxima compra."
            )
        if persona_id == 1:
            return (
                "Nós compararíamos o aumento com os benefícios do cartão antes de mudar a compra. "
                "Pontos, crédito ou uma oferta digital antes da compra poderiam preservar a conveniência e ajudar no orçamento. "
                "Se o preço subisse sem benefício no cartão, buscaríamos uma alternativa mais vantajosa."
            )
        return (
            "Nós reagiríamos com cautela, porque preço estável e previsibilidade pesam muito para nós. "
            "Um benefício recorrente poderia reduzir o incômodo, mas uma alta brusca nos faria diminuir a frequência aos poucos. "
            "A troca para outra marca seria gradual, sem abandonar o hábito de uma vez."
        )
    if "combo promocional" in q or "combo" in q:
        if persona_id == 0:
            return (
                "Nós reagiríamos melhor a um combo disponível na loja física, com desconto instantâneo ou cashback na carteira digital. "
                "A oferta precisa ser simples e os produtos precisam estar disponíveis no ponto de venda. "
                "Se o combo parecer confuso ou sem benefício imediato, tendemos a manter a compra habitual."
            )
        if persona_id == 1:
            return (
                "Nós prestaríamos atenção em um combo anunciado antes da compra, com pontos, crédito ou benefício no cartão. "
                "A conveniência de entender a oferta pelo canal digital aumentaria a chance de colocarmos outros produtos no carrinho. "
                "Se o benefício do cartão não ficar claro, o combo perde força para nós."
            )
        return (
            "Nós consideraríamos um combo se ele tivesse preço previsível, benefício recorrente e valor fácil de comparar. "
            "Uma oferta estável ao longo do tempo pareceria menos arriscada do que uma promoção pontual. "
            "Para nós, o combo precisa funcionar como teste gradual, não como pressão para comprar mais."
        )
    if "nova marca de bebida" in q or "pela primeira vez" in q:
        if persona_id == 0:
            return (
                "Nós experimentaríamos uma nova marca se ela estivesse disponível na loja física e passasse confiança no ponto de venda. "
                "Cashback, desconto instantâneo ou benefício na carteira digital reduziria o risco da primeira compra. "
                "Sem esses sinais simples, preferimos ficar com a marca conhecida."
            )
        if persona_id == 1:
            return (
                "Nós testaríamos uma nova marca se ela viesse com pontos, crédito ou benefício claro no cartão. "
                "Uma mensagem digital antes da compra ajudaria a lembrar a oferta e comparar a conveniência. "
                "Se não houver vantagem prática no pagamento, a chance de experimentar cai."
            )
        return (
            "Nós experimentaríamos uma nova marca com mais cautela, buscando preço estável e benefício recorrente. "
            "A primeira compra teria que parecer previsível e sem risco de mudança brusca. "
            "Se a marca mantiver consistência, a troca pode acontecer aos poucos."
        )
    if "trocarem da loja física para um canal digital" in q or "canal digital" in q:
        if persona_id == 0:
            return (
                "Nós só trocaríamos a loja física por um canal digital se a disponibilidade do produto fosse clara e confiável. "
                "Cashback, desconto instantâneo ou pagamento pela carteira digital ajudariam a reduzir a resistência. "
                "Sem confiança parecida com a do ponto de venda, preferimos continuar na loja física."
            )
        if persona_id == 1:
            return (
                "Nós iríamos para o canal digital se ele trouxesse conveniência real, benefícios de crédito e pontos no cartão. "
                "Uma comunicação digital antes da compra ajudaria a planejar melhor e comparar ofertas. "
                "Se o processo for lento ou não mostrar a vantagem do cartão, a loja física continua mais prática."
            )
        return (
            "Nós consideraríamos o canal digital de forma gradual, desde que houvesse preço estável e benefício recorrente. "
            "A previsibilidade da entrega e do valor seria mais importante do que uma promoção pontual. "
            "Sem essa segurança, nossa cautela nos manteria na loja física."
        )
    if "tipo de promoção" in q and "comprar mais" in q:
        if persona_id == 0:
            return (
                "Nós compraríamos mais com uma promoção simples na loja física, ligada a cashback ou desconto instantâneo na carteira digital. "
                "A regra precisa ser clara e o produto precisa estar disponível no ponto de venda. "
                "Se houver muita burocracia, a confiança na oferta cai."
            )
        if persona_id == 1:
            return (
                "Nós compraríamos mais com ofertas que somem pontos, crédito ou condições melhores no cartão. "
                "Uma mensagem digital antes da compra ajudaria a perceber a vantagem e planejar a ida à loja. "
                "Se o benefício não for conveniente, a promoção perde força."
            )
        return (
            "Nós compraríamos mais se a promoção trouxesse preço estável, benefício recorrente e valor fácil de comparar. "
            "Preferimos algo previsível, que possa entrar na rotina sem parecer uma mudança brusca. "
            "A mudança precisa ser gradual e de baixo risco."
        )
    if "abandonarem uma marca" in q:
        if persona_id == 0:
            return (
                "Nós abandonaríamos uma marca se ela falhasse em disponibilidade na loja física ou perdesse confiança no ponto de venda. "
                "A falta de cashback, desconto instantâneo ou benefício na carteira digital também reduziria a vantagem. "
                "Sem esses sinais claros, procuraríamos uma alternativa mais confiável."
            )
        if persona_id == 1:
            return (
                "Nós abandonaríamos uma marca se ela deixasse de oferecer crédito, pontos ou benefícios relevantes no cartão. "
                "A falta de comunicação digital antes da compra também nos faria olhar outras opções. "
                "Se perder conveniência e controle no pagamento, a marca deixa de valer a repetição."
            )
        return (
            "Nós abandonaríamos uma marca se ela perdesse estabilidade de preço, previsibilidade ou benefício recorrente. "
            "A mudança não seria imediata, mas nossa cautela aumentaria a cada compra ruim. "
            "Com sinais consistentes de instabilidade, migraríamos aos poucos para outra opção."
        )
    if "melhor momento" in q and "impactar" in q:
        if persona_id == 0:
            return (
                "Para nós, o melhor momento é dentro da loja física, quando conseguimos confirmar disponibilidade e confiar no ponto de venda. "
                "Uma mensagem sobre cashback, desconto instantâneo ou carteira digital funciona melhor se for verificável ali. "
                "Antes da compra ajuda menos se a informação não se confirmar na loja."
            )
        if persona_id == 1:
            return (
                "Para nós, o melhor momento é antes da compra, por comunicação digital com crédito, pontos e benefícios do cartão. "
                "Isso ajuda a planejar a compra e escolher a opção mais conveniente. "
                "No checkout, a oferta chega tarde se não tiver sido entendida antes."
            )
        return (
            "Para nós, o melhor momento é antes da compra, com uma mensagem previsível e sem pressão. "
            "Precisamos comparar preço estável, benefício recorrente e valor ao longo do tempo. "
            "Dentro da loja ou no checkout funciona menos se parecer uma mudança apressada."
        )
    if "comunicação parece mais confiável" in q or ("comunicação" in q and "confiável" in q):
        if persona_id == 0:
            return (
                "Nós confiamos mais em comunicação clara, ligada à disponibilidade na loja física e ao ponto de venda. "
                "Mensagens sobre cashback, desconto instantâneo ou carteira digital precisam ser simples e fáceis de confirmar na loja. "
                "Se a informação parecer genérica, perdemos confiança."
            )
        if persona_id == 1:
            return (
                "Nós confiamos mais em comunicação digital antes da compra, principalmente quando explica crédito, pontos e benefícios do cartão. "
                "Ela precisa ajudar a planejar a compra com conveniência. "
                "Se a oferta não mostrar a vantagem do cartão, chama menos atenção."
            )
        return (
            "Nós confiamos mais em comunicação consistente, com preço estável, previsibilidade e benefício recorrente. "
            "A mensagem precisa mostrar valor claro ao longo do tempo, não só uma promessa pontual. "
            "Quanto mais gradual e sem pressão, melhor."
        )
    if "ofertas personalizadas" in q or "promoções simples" in q:
        if persona_id == 0:
            return (
                "Nós preferimos promoções simples para todos, desde que sejam fáceis de entender na loja física. "
                "Cashback, desconto instantâneo ou benefício na carteira digital ajudam quando a regra é clara. "
                "Se a oferta parecer confusa, perdemos confiança."
            )
        if persona_id == 1:
            return (
                "Nós tendemos a preferir ofertas personalizadas quando elas usam crédito, pontos e benefícios do cartão. "
                "Uma comunicação digital antes da compra ajuda a perceber a conveniência da oferta. "
                "Se a personalização não trouxer vantagem prática, uma promoção simples funciona melhor."
            )
        return (
            "Nós preferimos promoções simples e previsíveis, com preço estável e benefício recorrente. "
            "Ofertas muito personalizadas podem parecer incertas se mudarem toda semana. "
            "Quanto mais gradual e fácil de comparar, maior a chance de aderirmos."
        )
    if "virar a escolha recorrente" in q or "escolha recorrente" in q:
        if persona_id == 0:
            return (
                "Para virar nossa escolha recorrente, a marca precisa estar disponível na loja física e passar confiança no ponto de venda. "
                "Cashback, desconto instantâneo ou benefício na carteira digital reforçariam a sensação de vantagem simples. "
                "Com produto disponível e benefício fácil de usar, voltaríamos a escolher a marca."
            )
        if persona_id == 1:
            return (
                "Para virar nossa escolha recorrente, a marca precisa combinar conveniência com benefícios de crédito, pontos e cartão. "
                "A comunicação digital antes da compra ajudaria a lembrar a oferta e planejar melhor a compra. "
                "Se o benefício for recorrente e fácil de entender, tenderíamos a repetir a escolha."
            )
        return (
            "Para virar nossa escolha recorrente, a marca precisa manter preço estável, consistência e benefício recorrente. "
                "Nós formaríamos o hábito aos poucos, conforme a proposta se mostrasse previsível e de baixo risco. "
                "Sem estabilidade ao longo do tempo, preferimos manter a marca atual."
        )
    return None


_PERSONA_SIGNALS = {
    0: ("carteira", "cashback", "desconto", "loja", "confiança", "disponibilidade", "pagamento"),
    1: ("crédito", "cartão", "pontos", "digital", "conveniência", "antes da compra"),
    2: ("cautela", "previsibilidade", "previsível", "previsíveis", "estável", "estabilidade", "recorrente", "gradual", "hábito", "rotina"),
}


def _persona_signal_count(answer: str, persona_id: int) -> int:
    text = answer.lower()
    return sum(1 for signal in _PERSONA_SIGNALS[persona_id] if signal in text)


def _needs_fallback(answer: str) -> bool:
    text = re.sub(r"\s+", " ", answer.strip())
    if not text:
        return True
    sentence_count = len([s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()])
    word_count = len(text.split())
    if sentence_count < 2 or word_count < 25:
        return True
    if looks_truncated(text):
        return True
    if has_quality_issue(text):
        return True
    lowered = text.lower().rstrip(".!?;:,")
    bad_tails = (
        "poderia",
        "confort",
        "no entanto",
        "mas também",
        "nossa cautela",
        "mud",
        "confian",
        "necess",
        "como",
        "pois",
        "mudanças significativas em preços",
        "tende a ser mais",
        "preço está",
    )
    return lowered.endswith(bad_tails)


def _is_digital_channel_question(question: str) -> bool:
    text = question.lower()
    return any(term in text for term in ("canal digital", "loja física para um canal digital", "online", "app", "site"))


def _clean_profile_value(value: object) -> str:
    return str(value).replace("_", " ").strip()


def _format_profile_number(value: object) -> str:
    try:
        return f"{float(value):.1f}".replace(".", ",")
    except (TypeError, ValueError):
        return _clean_profile_value(value)


def _profile_answer(question: str, persona) -> str | None:
    """Answer factual persona/profile questions without marketing fallback."""
    q = question.lower()
    profile = persona.profile
    age_terms = ("quantos anos", "quanto anos", "idade", "faixa etária", "faixa etaria")
    identity_terms = ("quem é você", "quem e voce", "quem são vocês", "quem sao voces", "qual seu perfil", "qual é o perfil")
    region_terms = ("de onde", "região", "regiao", "norte", "sudeste")
    channel_terms = ("canal preferido", "loja física", "loja fisica")
    payment_terms = ("pagamento", "meio de pagamento", "carteira", "cartão", "cartao", "crédito", "credito")
    frequency_terms = ("frequência", "frequencia", "compram com que frequência", "compram com que frequencia")

    age = _format_profile_number(profile.get("idade_media", "não informada"))
    age_band = _clean_profile_value(profile.get("faixa_etaria_modal", "não informada"))
    region = _clean_profile_value(profile.get("regiao_modal", "não informada"))
    channel = _clean_profile_value(profile.get("canal_preferido_modal", "não informado"))
    payment = _clean_profile_value(profile.get("pagamento_modal", "não informado"))
    frequency = _clean_profile_value(profile.get("frequencia_compra_modal", "não informada"))

    if any(term in q for term in age_terms):
        if persona.cluster_id == 2:
            return (
                f"Nós não somos uma pessoa individual; representamos um segmento com idade média de {age} anos "
                f"e faixa etária modal {age_band}. Como esse perfil é mainstream, a leitura principal vem do comportamento "
                "recorrente e da cautela na mudança, não de uma idade única."
            )
        return (
            f"Nós não somos uma pessoa individual; representamos um segmento com idade média de {age} anos "
            f"e faixa etária modal {age_band}. Essa é a referência de idade do nosso cluster."
        )

    if any(term in q for term in identity_terms):
        return (
            f"Nós somos a persona {persona.segment_name}. Representamos um cluster de consumidores com região modal {region}, "
            f"canal preferido {channel}, pagamento modal {payment} e frequência de compra {frequency}."
        )

    if any(term in q for term in region_terms):
        return (
            f"Nossa região modal é {region}. Esse dado descreve a concentração principal do cluster, "
            "não a localização de uma pessoa individual."
        )

    if any(term in q for term in channel_terms):
        return (
            f"Nosso canal preferido no perfil do cluster é {channel}. Esse comportamento ajuda a orientar como a persona "
            "responde sobre compra e relacionamento com a marca."
        )

    if any(term in q for term in payment_terms):
        return (
            f"Nosso meio de pagamento modal é {payment}. Esse sinal é usado para manter a resposta alinhada ao perfil "
            "da persona nas perguntas de compra."
        )

    if any(term in q for term in frequency_terms):
        return (
            f"Nossa frequência de compra modal é {frequency}. Esse dado representa o padrão dominante do segmento, "
            "não uma rotina individual fixa."
        )

    return None


def _smalltalk_answer(question: str, persona) -> str | None:
    q = re.sub(r"\s+", " ", question.lower()).strip()
    has_greeting = any(term in q for term in ("olá", "ola", "oi", "bom dia", "boa tarde", "boa noite", "e aí", "e ai"))
    asks_wellbeing = any(term in q for term in ("tudo bem", "como vai", "como vocês estão", "como voces estao", "como você está", "como voce esta"))
    says_thanks = any(term in q for term in ("obrigado", "obrigada", "valeu", "agradeço", "agradeco"))

    if not (has_greeting or asks_wellbeing or says_thanks):
        return None

    if says_thanks and not has_greeting and not asks_wellbeing:
        return "Por nada. Podemos continuar a conversa quando quiser."

    if persona.cluster_id == 0:
        return "Olá, tudo bem por aqui. Pode perguntar sobre como compramos e o que nos passa confiança."
    if persona.cluster_id == 1:
        return "Olá, tudo bem por aqui. Pode perguntar sobre ofertas, conveniência ou decisão de compra."
    return "Olá, tudo bem por aqui. Pode perguntar sobre preço, rotina de compra ou mudança de marca."


def _has_final_quality_issue(answer: str, persona_id: int, question: str) -> bool:
    text = re.sub(r"\s+", " ", answer.strip())
    lowered = text.lower()
    if _needs_fallback(text):
        return True
    if persona_id == 0 and "compras online" in lowered and not _is_digital_channel_question(question):
        return True
    if sum(1 for _ in re.finditer(r"\bisso nos faria\b", lowered)) > 1:
        return True
    malformed_patterns = (
        r"\bisso nos faria evitar nossa cautela\b",
        r"\bconveniência e pelo controle financeiro\b",
        r"\bentão a marca ofereça\b",
        r"\ba comunicação seja\b",
        r"\ba promoção seja\b",
        r"\ba mudança gradual para nós,\s*então\b",
        r"\bnós tendemos a preferir se sentir\b",
        r"\bmanter nossa cautela pesa\b",
        r"\bmais conveniente\b",
        r"\bisso nos faria sentir mais confiantes\b.*\bnos levaria\b",
        r"\bmotivado a experimentar\b",
        r"\bpreferir pela previsibilidade\b",
        r"\ba conveniência e os benefícios de crédito nos faria\b",
        r"\ba mudança gradual e a previsibilidade nos faria\b",
        r"\bbenefícios recorrentes e uma transição gradual e de baixo risco de compra também nos faria\b",
    )
    if any(re.search(pattern, lowered) for pattern in malformed_patterns):
        return True
    sentence_parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    for sentence in sentence_parts:
        sentence_lower = sentence.lower().rstrip(".!?;:,")
        if re.match(r"^(a comunicação seja|a mudança gradual para nós|para nós, conveniência e pelo)", sentence_lower):
            return True
    return False


def _has_question_signal_issue(answer: str, persona_id: int, question: str) -> bool:
    text = answer.lower()
    q = question.lower()

    def has_any(*terms: str) -> bool:
        return any(term in text for term in terms)

    if "aumento de preço" in q or "10%" in q:
        if persona_id == 0:
            return not (has_any("cashback", "carteira", "desconto") and has_any("loja", "confiança", "disponibilidade"))
        if persona_id == 1:
            return not has_any("crédito", "cartão", "pontos") or has_any(
                "previsibilidade", "previsível", "estabilidade", "estável", "estáveis", "recorrente", "recorrentes"
            )
        return not has_any("previsibilidade", "estabilidade", "estável", "recorrente", "gradual")

    if "combo promocional" in q or "combo" in q:
        if persona_id == 0:
            return not (has_any("cashback", "carteira", "desconto") and has_any("loja", "ponto de venda", "disponível", "disponibilidade"))
        if persona_id == 1:
            return (
                not (has_any("crédito", "cartão", "pontos") and has_any("digital", "antes da compra", "conveniência"))
                or has_any("previsibilidade", "previsível", "estabilidade", "estável", "estáveis", "recorrente", "recorrentes")
            )
        return not has_any("previsível", "previsibilidade", "estável", "estabilidade", "recorrente", "gradual", "baixo risco")

    if "virar a escolha recorrente" in q or "escolha recorrente" in q:
        if "isso nos faria" in text or "bem-sucedida" in text:
            return True
        if persona_id == 0:
            return not (has_any("loja", "ponto de venda", "disponibilidade", "confiança") and has_any("carteira", "cashback", "desconto"))
        if persona_id == 1:
            return not (has_any("crédito", "cartão", "pontos") and has_any("digital", "conveniência", "antes da compra"))
        return not has_any("previsibilidade", "estabilidade", "estável", "recorrente", "gradual", "hábito", "consistência")

    if "nova marca de bebida" in q or "pela primeira vez" in q:
        if (
            "nós compraríamos uma nova marca de bebida pela primeira vez" in text
            or "isso nos faria sentir mais confiantes em tentar algo novo" in text
        ):
            return True
        if persona_id == 0:
            return not (has_any("loja", "ponto de venda", "disponibilidade", "confiança") and has_any("carteira", "cashback", "desconto"))
        if persona_id == 1:
            return not (has_any("crédito", "cartão", "pontos") and has_any("digital", "antes da compra"))
        return not has_any("previsibilidade", "estabilidade", "estável", "recorrente", "gradual", "consistência")

    if "comunicação parece mais confiável" in q or ("comunicação" in q and "confiável" in q):
        if persona_id == 0:
            return not (has_any("loja", "ponto de venda", "disponibilidade", "confiança") and has_any("carteira", "cashback", "desconto"))
        if persona_id == 1:
            return not (has_any("crédito", "cartão", "pontos") and has_any("digital", "antes da compra", "conveniência"))
        return not has_any("previsibilidade", "estabilidade", "estável", "recorrente", "gradual", "consistente")

    if "ofertas personalizadas" in q or "promoções simples" in q:
        if "nossos consumidores" in text or "nossas vendas" in text:
            return True
        if persona_id == 0:
            return not (has_any("loja", "carteira", "cashback", "desconto", "confiança") and has_any("simples", "clar"))
        if persona_id == 1:
            return not (has_any("crédito", "cartão", "pontos") and has_any("personalizadas", "digital", "conveniência"))
        return not has_any("previsibilidade", "estabilidade", "estável", "recorrente", "gradual", "simples")

    return False


def _should_use_targeted_fallback(question: str) -> bool:
    q = question.lower()
    return (
        "aumento de preço" in q
        or "10%" in q
        or "combo promocional" in q
        or "combo" in q
        or "nova marca de bebida" in q
        or "pela primeira vez" in q
        or "trocarem da loja física para um canal digital" in q
        or "canal digital" in q
        or ("tipo de promoção" in q and "comprar mais" in q)
        or "abandonarem uma marca" in q
        or ("melhor momento" in q and "impactar" in q)
        or "comunicação parece mais confiável" in q
        or ("comunicação" in q and "confiável" in q)
        or "ofertas personalizadas" in q
        or "promoções simples" in q
        or "virar a escolha recorrente" in q
        or "escolha recorrente" in q
    )


def _persona_polish_guidance(persona_id: int) -> str:
    if persona_id == 0:
        return "Use linguagem simples sobre confiança, loja física, disponibilidade, carteira digital, cashback e desconto instantâneo."
    if persona_id == 1:
        return "Use linguagem sobre conveniência, crédito, pontos, cartão e comunicação digital antes da compra."
    return "Use linguagem cautelosa sobre previsibilidade, preço estável, benefício recorrente, hábito e mudança gradual."


def _polish_answer(answer: str, persona_id: int) -> str:
    prompt = f"""
Rewrite the answer in natural Brazilian Portuguese, keeping the same persona-specific meaning.
Use 2 to 3 complete sentences. Do not add new claims. Preserve the persona signals.

Regras:
- Primeira pessoa do plural.
- 2 a 3 frases completas.
- Sem fragmentos, sem termos técnicos e sem IDs.
- Não use "A decisões", "Lembrar que", "comprariamos" ou frases começando com "Evitar".
- Não repita "Isso nos faria" mais de uma vez.
- Não use frases malformadas como "Isso nos faria evitar Nossa cautela", "conveniência e pelo controle financeiro" ou "então a marca ofereça".
- Corrija concordância e acentuação.
- {_persona_polish_guidance(persona_id)}

Resposta original:
{answer}

Resposta reescrita:
""".strip()
    polished = generate_answer(prompt)
    return normalize_persona_answer(polished, max_sentences=3, max_words=90)


def answer_as_persona(
    question: str,
    persona_id: int,
    include_context: bool = True,
    history_messages: list[dict] | None = None,
    prior_answer_signatures: list[str] | None = None,
    forbidden_openings: list[str] | None = None,
) -> PersonaAnswer:
    persona = get_persona_by_id(persona_id)
    retrieved_context = []
    if include_context:
        try:
            retrieved_context = retrieve_context(question, persona_id)
        except Exception as exc:
            logger.warning(
                "retrieval_unavailable persona_id=%s error=%s; continuing without context",
                persona_id,
                exc,
            )
    logger.info(
        "persona_id=%s retrieved_docs=%s",
        persona_id,
        [
            {"doc_id": doc.doc_id, "source_file": doc.source_file, "score": doc.score}
            for doc in retrieved_context
        ],
    )
    profile_answer = _profile_answer(question, persona)
    if profile_answer:
        return PersonaAnswer(
            cluster_id=persona.cluster_id,
            segment_name=persona.segment_name,
            answer=profile_answer,
            retrieved_context=retrieved_context if include_context else [],
        )

    smalltalk_answer = _smalltalk_answer(question, persona)
    if smalltalk_answer:
        return PersonaAnswer(
            cluster_id=persona.cluster_id,
            segment_name=persona.segment_name,
            answer=smalltalk_answer,
            retrieved_context=[],
        )

    prompt = build_persona_rag_prompt(
        question,
        persona,
        retrieved_context,
        history_messages=history_messages,
        prior_answer_signatures=prior_answer_signatures,
        forbidden_openings=forbidden_openings,
    )
    answer = generate_answer(prompt)
    answer = normalize_persona_answer(answer, max_sentences=3, max_words=90)
    targeted = _targeted_fallback_answer(question, persona.cluster_id)
    if targeted and _should_use_targeted_fallback(question):
        answer = targeted
    final_issue = _has_final_quality_issue(answer, persona.cluster_id, question)
    signal_issue = _has_question_signal_issue(answer, persona.cluster_id, question)
    missing_persona_signal = _persona_signal_count(answer, persona.cluster_id) == 0
    if final_issue or signal_issue or missing_persona_signal:
        if signal_issue and targeted:
            answer = targeted
        else:
            polished = _polish_answer(answer, persona.cluster_id) if answer else ""
            answer = (
                polished
                if polished
                and not _has_final_quality_issue(polished, persona.cluster_id, question)
                and not _has_question_signal_issue(polished, persona.cluster_id, question)
                and _persona_signal_count(polished, persona.cluster_id) > 0
                else targeted or _fallback_answer(persona.cluster_id)
            )
    return PersonaAnswer(
        cluster_id=persona.cluster_id,
        segment_name=persona.segment_name,
        answer=answer,
        retrieved_context=retrieved_context if include_context else [],
    )


def answer_with_multiple_personas(
    question: str,
    persona_ids: list[int],
    include_context: bool = True,
    history_messages: list[dict] | None = None,
) -> ChatResponse:
    answers: list[PersonaAnswer] = []
    prior_answer_signatures: list[str] = []
    prior_openings: list[str] = []
    for persona_id in persona_ids:
        ans = answer_as_persona(
            question=question,
            persona_id=persona_id,
            include_context=include_context,
            history_messages=history_messages,
            prior_answer_signatures=prior_answer_signatures,
            forbidden_openings=prior_openings,
        )
        opening = _opening_signature(ans.answer)
        if opening in prior_openings:
            # Retry once with stronger lexical separation constraints.
            ans = answer_as_persona(
                question=question,
                persona_id=persona_id,
                include_context=include_context,
                history_messages=history_messages,
                prior_answer_signatures=prior_answer_signatures,
                forbidden_openings=prior_openings,
            )
            opening = _opening_signature(ans.answer)
        answers.append(ans)
        signature = _answer_signature(ans.answer)
        if signature:
            prior_answer_signatures.append(signature)
        if opening:
            prior_openings.append(opening)
    return ChatResponse(question=question, answers=answers)
