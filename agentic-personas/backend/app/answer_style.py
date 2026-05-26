from __future__ import annotations

import re


_FILLER_PATTERNS = [
    r"\bé importante considerar que\b",
    r"\bé importante considerar\b",
    r"\bé importante notar que\b",
    r"\bé importante notar\b",
    r"\bé fundamental considerar que\b",
    r"\bé fundamental considerar\b",
    r"\bé importante que\b",
    r"\bé importante\b",
    r"\bno entanto\b",
    r"\bpode indicar que\b",
    r"\bo que pode indicar que\b",
    r"\bo que pode indicar\b",
    r"\bo que sugere que\b",
]

_TECHNICAL_REWRITES = [
    (
        r"\bmarca_00\b",
        "marca atual",
    ),
    (
        r"\bmarca_01\b",
        "marca concorrente",
    ),
    (
        r"\bmarca_\d+\b",
        "marca concorrente",
    ),
    (
        r"\binfluencer_\d+\b",
        "influenciador relevante",
    ),
    (
        r"\bNossa escolha recorrente é ser influenciad[oa]s?\b",
        "Nós tendemos a ser influenciados",
    ),
    (
        r"\bNossa escolha recorrente é comprar\b",
        "Nós costumamos comprar",
    ),
    (
        r"\bNossa escolha recorrente de bebidas é influenciada\b",
        "Nossa escolha de bebidas é influenciada",
    ),
    (
        r"\bNossa escolha recorrente de bebidas tende\b",
        "Nossa escolha de bebidas tende",
    ),
    (
        r"\bNossa escolha recorrente de bebidas em\b",
        "Nossa preferência por bebidas em",
    ),
    (
        r"\bNossa escolha recorrente de comprar\b",
        "Nossa preferência por comprar",
    ),
    (
        r"\bNossa escolha recorrente por\b",
        "Nossa preferência por",
    ),
    (
        r"\bNossa escolha recorrente mudaria\b",
        "Nós mudaríamos nossa escolha",
    ),
    (
        r"\bNossa escolha recorrente tende\b",
        "Nossa decisão tende",
    ),
    (
        r"\bNossa escolha recorrente é\b",
        "Nós tendemos a preferir",
    ),
    (
        r"\bNós tendemos a preferir baseada em\b",
        "Nossa decisão tende a se basear em",
    ),
    (
        r"\bNós tendemos a preferir por\b",
        "Nós tendemos a preferir",
    ),
    (
        r"\bNós tendemos a preferir influenciada por\b",
        "Nossa decisão tende a ser influenciada por",
    ),
    (
        r"\bNós tendemos a preferir influenciada pela\b",
        "Nossa decisão tende a ser influenciada pela",
    ),
    (
        r"\bNós tendemos a preferir influenciada pelo\b",
        "Nossa decisão tende a ser influenciada pelo",
    ),
    (
        r"\bse oferecermos crédito\b",
        "se o combo oferecer crédito",
    ),
    (
        r"\bse oferecermos benefícios\b",
        "se a oferta trouxer benefícios",
    ),
    (
        r"\bse oferecermos cashback\b",
        "se o combo oferecer cashback",
    ),
    (
        r"\bse oferecermos desconto\b",
        "se o combo oferecer desconto",
    ),
    (
        r"\bpara nos manterem leais\b",
        "para manter nossa preferência",
    ),
    (
        r"\bmanter esses aspectos em mente\b",
        "manter esses sinais claros para nós",
    ),
    (
        r"\bNós tendemos a preferir buscar\b",
        "Nós tendemos a buscar",
    ),
    (
        r"\bobstáculo para nossa escolha recorrente\b",
        "obstáculo para nossa decisão",
    ),
    (
        r"\bpreço está\.",
        "preço estável.",
    ),
    (
        r"\bobstá\.",
        "obstáculo.",
    ),
    (
        r"\bmensagens confusas\b",
        "comunicação pouco clara",
    ),
    (
        r"\bMas evitar comunicação pouco clara\b",
        "Também precisamos evitar comunicação pouco clara",
    ),
    (
        r"\bMas precisamos evitar comunicação pouco clara\b",
        "Também precisamos evitar comunicação pouco clara",
    ),
    (
        r"Como nosso perfil é mais mainstream, a decisão tende a ser mais\.",
        "Como nosso perfil é mais mainstream, a decisão tende a ser mais cautelosa e gradual.",
    ),
    (
        r"Mas Como nosso perfil é mais mainstream, a decisão tende a ser mais cautelosa e gradual\.a decisão tende a ser mais cautelosa e gradual\.",
        "Como nosso perfil é mais mainstream, a decisão tende a ser mais cautelosa e gradual.",
    ),
    (
        r"Como nosso perfil é mais mainstream,\s*a decisão tende a ser mais cautelosa e gradual\.",
        "Como nosso perfil é mais mainstream, a decisão tende a ser mais cautelosa e gradual.",
    ),
    (
        r"\bMas Como\b",
        "Como",
    ),
    (
        r"\bbaixo fricção\b",
        "baixa fricção",
    ),
    (
        r"\bcautelosos e gradual\b",
        "cautelosos e graduais",
    ),
    (
        r"\brecordatorias\b",
        "lembretes",
    ),
    (
        r"\bNós evitaria\b",
        "Nós evitaríamos",
    ),
    (
        r"\bnós evitaria\b",
        "nós evitaríamos",
    ),
    (
        r"Para virar a escolha recorrente de nós",
        "Para virar nossa escolha recorrente",
    ),
    (
        r"escolha recorrente de nós",
        "nossa escolha recorrente",
    ),
    (
        r"\bo melhor momento para impactar nós seríamos\b",
        "o melhor momento para nos impactar seria",
    ),
    (
        r"\bpara impactar nós seríamos\b",
        "para nos impactar seria",
    ),
    (
        r"\bpara impactar nós seria\b",
        "para nos impactar seria",
    ),
    (
        r"\bimpactar nós seríamos\b",
        "nos impactar seria",
    ),
    (
        r"\bimpactar nós seria\b",
        "nos impactar seria",
    ),
    (
        r"\bimpactar nós\b",
        "nos impactar",
    ),
    (
        r"\bA possibilidade de nos impactar no checkout, onde a conveniência e a simplicidade do processo de pagamento são cruciais\.",
        "No checkout, a conveniência e a simplicidade do pagamento também poderiam pesar.",
    ),
    (
        r"\bEvitar comunicação pouco clara que possam\b",
        "Evitaríamos comunicações pouco claras que possam",
    ),
    (
        r"\bevitar comunicação pouco clara que possam\b",
        "evitaríamos comunicações pouco claras que possam",
    ),
    (
        r"\bA comunicação digital antes da compra também para nós\.",
        "A comunicação digital antes da compra também pesa para nós.",
    ),
    (
        r"\bA comunicação digital antes da compra para nós\.",
        "A comunicação digital antes da compra pesa para nós.",
    ),
    (
        r"\bNós tendemos a preferir ser impactada por mensagens\b",
        "Nós prestaríamos mais atenção a mensagens",
    ),
    (
        r"\bNós tendemos a preferir ser atraída por mensagens\b",
        "Nós prestaríamos mais atenção a mensagens",
    ),
    (
        r"\bIsso nos impactar, pois\b",
        "Isso nos impactaria, pois",
    ),
    (
        r"\bIsso nos impactar, especialmente\b",
        "Isso nos impactaria, especialmente",
    ),
    (
        r"\bIsso nos impactar mais do que\b",
        "Isso pesa mais para nós do que",
    ),
    (
        r"\bIsso nos impactar e nos fazer\b",
        "Isso nos impactaria e nos faria",
    ),
    (
        r"\bpois nos impactar a facilidade e a rapidez do processo de compra\b",
        "pois valorizamos a facilidade e a rapidez do processo de compra",
    ),
    (
        r"\bIsso nos ajuda a evitar comunicação pouco clara e nos permite\b",
        "Isso torna a oferta mais fácil de entender e nos permite",
    ),
    (
        r"\bA disponibilidade do produto e a confiança no ponto de venda, pois esses fatores nos impactam mais do que descontos imediatos ou pontos\.",
        "A disponibilidade do produto e a confiança no ponto de venda também pesam na nossa decisão.",
    ),
    (
        r"\bEvitar comunicação pouco clara e manter a comunicação clara sobre benefícios\.",
        "A comunicação sobre benefícios precisa ser simples e direta.",
    ),
    (
        r"\bEvitar comunicação pouco clara sobre benefícios, pois isso pode nos confundir\.",
        "A comunicação sobre benefícios precisa ser clara para não gerar dúvida.",
    ),
    (
        r"\bEvitar comunicação pouco clara e focar em ofertas claras e convincentes\.",
        "Preferimos ofertas claras e convincentes.",
    ),
    (
        r"\bEvitar comunicação pouco clara e focar em ofertas claras e diretas\.",
        "Preferimos ofertas claras e diretas.",
    ),
    (
        r"\bEvitar comunicação pouco clara e focar em comunicação clara sobre os benefícios\.",
        "A comunicação precisa explicar os benefícios com clareza.",
    ),
    (
        r"\bMas,\s*evitar comunicação pouco clara e garantir que a oferta seja clara e fácil de entender\.",
        "A oferta precisa ser clara e fácil de entender.",
    ),
    (
        r"\bEvitar comunicação pouco clara e oferecer clareza sobre os benefícios\.",
        "A oferta precisa deixar os benefícios claros.",
    ),
    (
        r"\bEvitar comunicação pouco clara e garantir que as informações sejam claras e precisas\.",
        "As informações precisam ser claras e precisas.",
    ),
    (
        r"\bEvitar comunicação pouco clara e garantir que a comunicação seja clara e relevante para nós\.",
        "A comunicação precisa ser clara e relevante para nós.",
    ),
    (
        r"\bLembrar que a confiança no ponto de venda é fundamental para nossa decisão de compra, então é melhor evitar comunicação pouco clara e garantir que a comunicação seja clara e simples\.",
        "A confiança no ponto de venda é fundamental, então a comunicação precisa ser clara e simples.",
    ),
    (
        r"\bEvitar comunicação pouco clara e garantir que as ofertas sejam claras e atraentes para nós\.",
        "As ofertas precisam ser claras e atraentes para nós.",
    ),
    (
        r"\bEvitar comunicação pouco clara e focar em benefícios claros e objetivos\.",
        "Preferimos benefícios claros e objetivos.",
    ),
    (
        r"\bNós tendemos a preferir feita dentro da loja\b",
        "Preferimos ser impactados dentro da loja",
    ),
    (
        r"\bTer comunicação clara sobre benefícios e incentivos financeiros simples para nos convencer\.",
        "Comunicação clara sobre benefícios e incentivos financeiros simples pode nos convencer.",
    ),
    (
        r"\bentão a conveniência e a previsibilidade\.",
        "então a conveniência e os benefícios do cartão precisam ficar claros.",
    ),
    (
        r"\bEvitar comunicação pouco clara e garantir que as ofertas sejam claras e atraentes\.",
        "Evitaríamos comunicações pouco claras; as ofertas precisam ser diretas e atraentes.",
    ),
    (
        r"\bLembrar que nossa decisão tende a ser mais cautelosa e gradual,?\.?",
        "Nossa decisão tende a ser mais cautelosa e gradual.",
    ),
    (
        r"\bLembrar que a mudança gradual é fundamental para nós,?\s*então qualquer impacto deve ser gradual e não abrupto\.",
        "Para nós, a mudança precisa ser gradual e sem pressão.",
    ),
    (
        r"\bLembrar que\b",
        "Para nós,",
    ),
    (
        r"\bA cautela em nossas decisões de compra\.",
        "Nossa cautela pesa na decisão de compra.",
    ),
    (
        r"\bA cautela em nossas decisões de compra nos faria evitar mudanças abruptas\.",
        "Nossa cautela nos faria evitar mudanças abruptas.",
    ),
    (
        r"\bA cautela em nossas decisões de compra nos faz evitar mudanças abruptas\.",
        "Nossa cautela nos faz evitar mudanças abruptas.",
    ),
    (
        r"\bNós valorizamos a cautela em nossas decisões de compra\b",
        "Nós valorizamos decisões cautelosas",
    ),
    (
        r"\bA cautela em nossas decisões de compra\b",
        "Nossa cautela",
    ),
    (
        r"\ba cautela em nossas decisões de compra\b",
        "nossa cautela",
    ),
    (
        r"\bcautela em nossas decisões de compra\b",
        "cautela nas compras",
    ),
    (
        r"\bA decisões cautelosas nos faria\b",
        "Nossa cautela nos faria",
    ),
    (
        r"\bA decisões cautelosas nos faz\b",
        "Nossa cautela nos faz",
    ),
    (
        r"\bA decisões cautelosas nos leva\b",
        "Nossa cautela nos leva",
    ),
    (
        r"\bA decisões cautelosas\b",
        "Decisões mais cautelosas",
    ),
    (
        r"\bNós comprariamos\b",
        "Nós compraríamos",
    ),
    (
        r"\bnós comprariamos\b",
        "nós compraríamos",
    ),
    (
        r"\bA conveniência, mas não mais do que a confiança e a disponibilidade\.",
        "A conveniência importa, mas confiança e disponibilidade pesam mais para nós.",
    ),
    (
        r"\bIsso nos faria abandonar a marca\.",
        "Isso poderia nos levar a trocar de marca.",
    ),
    (
        r"\bIsso nos faria escolher essa opção em vez de outras\.",
        "Isso tornaria a opção mais atraente para nós.",
    ),
    (
        r"\bNossa decisão tende a ser influenciada por esses fatores, então atender a essas necessidades para manter nossa lealdade\.",
        "A marca precisaria atender a essas necessidades para manter nossa preferência.",
    ),
    (
        r"\bNossa decisão tende a ser influenciada pela ([^.]+)\.",
        r"Para nós, \1 pesa mais.",
    ),
    (
        r"\bNossa decisão tende a ser influenciada pelo ([^.]+)\.",
        r"Para nós, \1 pesa mais.",
    ),
    (
        r"\bNossa decisão tende a ser influenciada por ([^.]+)\.",
        r"Para nós, pesam mais \1.",
    ),
    (
        r"\bNossa decisão tende a ser influenciada pela\b",
        "Para nós, pesa mais a",
    ),
    (
        r"\bNossa decisão tende a ser influenciada pelo\b",
        "Para nós, pesa mais o",
    ),
    (
        r"\bNossa decisão tende a ser influenciada por\b",
        "Para nós, pesam mais",
    ),
    (
        r"\be pelos benefícios\b",
        "e os benefícios",
    ),
    (
        r"\be por ofertas\b",
        "e ofertas",
    ),
    (
        r"\bantes da compra antes da compra\b",
        "antes da compra",
    ),
    (
        r"\bpois Nossa decisão\b",
        "pois nossa decisão",
    ),
    (
        r"\bestabilidade de preço garantido\b",
        "estabilidade de preço",
    ),
    (
        r"\bgarantido\b",
        "claro",
    ),
    (
        r"\bEvitar riscos e fricções, como mudanças bruscas nos preços ou na qualidade da bebida\.",
        "Nós evitaríamos mudanças bruscas nos preços ou na qualidade da bebida.",
    ),
    (
        r"\bEvitar surpresas de preços e garantir a previsibilidade dos nossos gastos\.",
        "Nós evitaríamos surpresas de preço e buscaríamos previsibilidade nos gastos.",
    ),
    (
        r"\bEvitar ofertas confusas que possam nos confundir\.",
        "Nós evitaríamos ofertas confusas.",
    ),
    (
        r"\bA disponibilidade dos produtos seja garantida e que a comunicação sobre os benefícios seja clara\.",
        "Precisamos encontrar os produtos disponíveis e entender os benefícios com clareza.",
    ),
    (
        r"\bEvitar a confusão de oferecer benefícios que não sejam claros e simples, pois isso pode nos afastar\.",
        "Benefícios pouco claros podem nos afastar.",
    ),
    (
        r"\bentão essa preferência ao planejar a estratégia de impacto\.",
        "Essa preferência pesa antes da compra.",
    ),
    (
        r"\bLembrar que nossa cautela e preferência por pre\.",
        "Nossa cautela e preferência por previsibilidade reduzem decisões por pressão.",
    ),
    (
        r"\bLembrar que a cautela é uma característica nossa, então não podemos dizer com certeza que somos mais influenciados por um fator em particular\.",
        "Nossa cautela é uma característica do perfil, então reagimos melhor a ofertas previsíveis.",
    ),
    (
        r"\bLembrar que nossa cautela e tendência a mudanças graduais podem influenciar a decisão\.",
        "Nossa cautela e tendência a mudanças graduais influenciam a decisão.",
    ),
    (
        r"\bEvitar a confusão e oferecer comunicação clara sobre benefícios\.",
        "A oferta precisa ser simples e clara sobre os benefícios.",
    ),
    (
        r"\bNossa decisão tende a ser influenciada por esses fatores, então atender às nossas necessidades\.",
        "Esses fatores pesam para nós, então a marca precisaria atender a essas necessidades.",
    ),
    (
        r"\buma cautela gradual em nossas decisões\b",
        "uma transição gradual e de baixo risco",
    ),
    (
        r"\bentão não sobressalhar em nossas expectativas\.",
        "então mudanças bruscas ou promessas pontuais nos afastariam.",
    ),
    (
        r"\bMudanças significativas em preços\.",
        "Mudanças significativas de preço pesariam na nossa decisão.",
    ),
    (
        r"\bUma oferta que nos permita mud\.",
        "Uma oferta que reduza risco pode facilitar uma mudança gradual.",
    ),
    (
        r"\bA falta de confian\.",
        "A falta de confiança seria uma barreira.",
    ),
    (
        r"\bComo\.",
        "Como nosso perfil é mais mainstream, a decisão tende a ser mais cautelosa e gradual.",
    ),
    (
        r"Como nosso perfil é mais mainstream,\s*\.",
        "Como nosso perfil é mais mainstream, a decisão tende a ser mais cautelosa e gradual.",
    ),
    (
        r"nós seria\b",
        "nós seríamos",
    ),
    (
        r"nós precisa\b",
        "nós precisamos",
    ),
    (
        r"nos ajudam a man\.",
        "nos ajudam a manter previsibilidade.",
    ),
    (
        r"\bMudanças graduais e sem riscos nos faria\b",
        "Mudanças graduais e de baixo risco nos fariam",
    ),
    (
        r"\bIsso nos faria evitar Nossa cautela\b",
        "Isso nos ajudaria a manter nossa cautela",
    ),
    (
        r"\be Nossa cautela\b",
        "e nossa cautela",
    ),
    (
        r"\bnos faria sentir mais confiança\b",
        "nos faria sentir mais confiantes",
    ),
    (
        r"\bmais confiantes e conforto\b",
        "mais confiantes e confortáveis",
    ),
    (
        r"\bIsso nos faz sentir mais confiança\b",
        "Isso nos deixa mais confiantes",
    ),
    (
        r"\bIsso nos faria sentir mais conveniência\b",
        "Isso nos daria mais conveniência",
    ),
    (
        r"\bIsso nos faria sentir mais conveniente\b",
        "Isso nos traria mais conveniência",
    ),
    (
        r"\bIsso nos traria mais conveniência e motivado a experimentar algo novo\b",
        "Isso nos traria mais conveniência e nos motivaria a experimentar algo novo",
    ),
    (
        r"\bnos traria mais conveniência e motivado\b",
        "nos traria mais conveniência e nos motivaria",
    ),
    (
        r"\bIsso nos faz sentir mais conveniência\b",
        "Isso nos dá mais conveniência",
    ),
    (
        r"\bnos faria sentir mais confortável\b",
        "nos faria sentir mais confortáveis",
    ),
    (
        r"\bIsso nos faria sentir mais confortável\b",
        "Isso nos faria sentir mais confortáveis",
    ),
    (
        r"\bque nos faça entender os benefícios de forma simples e fácil de entender\b",
        "que explique os benefícios de forma simples",
    ),
    (
        r"\bcomunicação pouco clara ou que não sejam relevantes\b",
        "comunicações pouco claras ou pouco relevantes",
    ),
    (
        r"\bNós evitaríamos comunicação pouco clara\b",
        "Nós evitaríamos comunicações pouco claras",
    ),
    (
        r"\bmais propensos a recomendar a ela\b",
        "mais propensos a continuar comprando",
    ),
    (
        r"\bNossa cautela em mudanças graduais pode levar a uma análise mais cuidadosa das ofertas personalizadas\.",
        "Nossa cautela faz com que avaliemos ofertas personalizadas com mais cuidado.",
    ),
    (
        r"\bPrecisamos ter certeza de que Precisamos\b",
        "Precisamos",
    ),
    (
        r"\bA comunicação seja clara e direta\b",
        "A comunicação precisa ser clara e direta",
    ),
    (
        r"\bA mudança gradual para nós, então\b",
        "Como preferimos mudança gradual,",
    ),
    (
        r"\bPara nós, conveniência e pelo controle financeiro\b",
        "Para nós, conveniência e controle financeiro",
    ),
    (
        r"\bentão a marca ofereça\b",
        "então a marca precisa oferecer",
    ),
    (
        r"\bNós tendemos a preferir se sentir confiantes em\b",
        "Nós tendemos a confiar mais em",
    ),
    (
        r"\bNós tendemos a preferir pela previsibilidade\b",
        "Nós tendemos a preferir previsibilidade",
    ),
    (
        r"\btendemos a preferir pela previsibilidade\b",
        "tendemos a preferir previsibilidade",
    ),
    (
        r"\bBenefícios recorrentes e uma transição gradual e de baixo risco de compra também nos faria considerar\b",
        "Benefícios recorrentes e uma transição gradual de baixo risco também nos fariam considerar",
    ),
    (
        r"\bA conveniência e os benefícios de crédito nos faria\b",
        "A conveniência e os benefícios de crédito nos fariam",
    ),
    (
        r"\bA mudança gradual e a previsibilidade nos faria\b",
        "A mudança gradual e a previsibilidade nos fariam",
    ),
    (
        r"\bpreço estável nos faria\b",
        "preço estável nos fariam",
    ),
    (
        r"\bmanter Nossa cautela\b",
        "manter nossa cautela",
    ),
    (
        r"\bdiminuisse\b",
        "diminuísse",
    ),
    (
        r"\bIsso nos faz sentir mais confiáveis\b",
        "Isso nos faz sentir mais confiantes",
    ),
    (
        r"\bpodemos se sentir\b",
        "podemos nos sentir",
    ),
    (
        r"\bmais valorizado e incentivado\b",
        "mais valorizados e incentivados",
    ),
    (
        r"\bmais confortável e conectado\b",
        "mais confortáveis e conectados",
    ),
    (
        r"às nossas necess\.",
        "às nossas necessidades.",
    ),
    (
        r"pode afetar nossas vendas",
        "pode nos levar a buscar alternativas mais acessíveis",
    ),
    (
        r"perda de clientes",
        "mudança para alternativas mais acessíveis",
    ),
    (
        r"fornecedor atual",
        "marca atual",
    ),
    (
        r"confiança dos nossos consumidores",
        "nossa confiança",
    ),
    (
        r"nossos consumidores",
        "nós",
    ),
    (
        r"clientes",
        "consumidores",
    ),
    (
        r"nosso público-alvo",
        "nosso perfil",
    ),
    (
        r"Uma mudança significativa na categoria bebidas exigiria uma análise cuidadosa das opções disponíveis",
        "Nós só mudaríamos se a nova opção parecesse realmente melhor e mais segura no dia a dia",
    ),
    (
        r"A marca tenha produtos de alta qualidade",
        "A marca precisaria ter produtos de qualidade",
    ),
    (
        r"produtos de alta qualidade e disponibilidade garantida",
        "produtos de qualidade e boa disponibilidade",
    ),
    (
        r"\bprodutos de alta qualidade\b",
        "produtos confiáveis",
    ),
    (
        r"Evitar mensagens que possam ser consideradas como um risco ou obstáculo para a compra",
        "Preferimos mensagens claras que reduzam a percepção de risco na compra",
    ),
    (
        r"Evitar riscos de fraude e garantir que os benefícios sejam claros e fáceis de entender",
        "Precisamos de benefícios claros e fáceis de entender, sem sensação de risco",
    ),
    (
        r"Mas reduzir a fricção de pagamento para que a mudança seja atraente",
        "A mudança precisa reduzir a fricção no pagamento para ser atraente",
    ),
    (
        r"credit-related benefits",
        "benefícios ligados ao crédito",
    ),
    (
        r"recordatorios",
        "lembretes",
    ),
    (
        r"compra semanais",
        "compras semanais",
    ),
    (
        r"\bbundles\b",
        "combos",
    ),
    (
        r"combo promocionais",
        "combos promocionais",
    ),
    (
        r"A parcelação",
        "O parcelamento",
    ),
    (
        r"essa é uma característica da nossa região e não há evidências fortes de que isso seja o principal motivador",
        "nosso perfil é mais mainstream, então a decisão tende a ser mais cautelosa e gradual",
    ),
    (
        r"a falta de diferenciação estatística em relação à base geral sugere que",
        "como nosso perfil é mais mainstream,",
    ),
    (
        r"(?:a\s+)?menor diferenciação estatística em relação à base geral",
        "nosso perfil mais mainstream",
    ),
    (
        r"diferenciação estatística",
        "diferença de perfil",
    ),
    (
        r"não há evidências fortes de que isso seja o principal motivador",
        "o sinal não é forte o bastante para tratar isso como único motivador",
    ),
    (
        r"característica da nossa região",
        "característica do nosso perfil",
    ),
    (
        r"a preferência por loja física,\s*o que pode indicar uma tendência a comprar com base em hábitos e familiaridade",
        "a preferência por loja física reforça hábitos e familiaridade",
    ),
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

_VERB_LIKE_PATTERN = re.compile(
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

_QUALITY_ISSUE_PATTERNS = [
    r"\ba decisões\b",
    r"\bcomprariamos\b",
    r"\blembrar que\b",
    r"\ba conveniência,\s*mas\b",
    r"\bevitar comunicação pouco clara\b",
    r"\bnossa decisão tende a ser influenciada\b",
    r"\bnos faria sentir mais confiança\b",
    r"\bnos faz sentir mais confiança\b",
    r"\bpodemos se sentir\b",
    r"\bmais valorizado e incentivado\b",
    r"\bseja garantida e que\b",
    r"\bmudanças graduais e sem riscos nos faria\b",
    r"\bcomunicação pouco clara ou que não sejam relevantes\b",
    r"\bisso nos faz sentir mais conveniência\b",
    r"\bmais propensos a recomendar a ela\b",
    r"\bnossa cautela em mudanças graduais\b",
    r"\bisso nos faria sentir mais confiantes\b.*\bnos levaria\b",
    r"\bprecisamos ter certeza de que precisamos\b",
    r"\bisso nos faria evitar nossa cautela\b",
    r"\bconveniência e pelo controle financeiro\b",
    r"\bentão a marca ofereça\b",
    r"\ba comunicação seja\b",
    r"\ba mudança gradual para nós, então\b",
    r"\bnós tendemos a preferir se sentir\b",
    r"\bmanter nossa cautela pesa\b",
    r"\bmais conveniente\b",
    r"\bmotivado a experimentar\b",
    r"\bpreferir pela previsibilidade\b",
    r"\bbenefícios recorrentes e uma transição gradual e de baixo risco de compra também nos faria\b",
    r"\ba conveniência e os benefícios de crédito nos faria\b",
    r"\ba mudança gradual e a previsibilidade nos faria\b",
]


def _clean_fillers(text: str) -> str:
    output = text
    for pattern, replacement in _TECHNICAL_REWRITES:
        output = re.sub(pattern, replacement, output, flags=re.IGNORECASE)
    for pattern in _FILLER_PATTERNS:
        output = re.sub(pattern, "", output, flags=re.IGNORECASE)
    output = re.sub(r"\bNo entanto,\s*,?", "Mas ", output, flags=re.IGNORECASE)
    output = re.sub(r"\bAlém disso,\s*,?", "", output, flags=re.IGNORECASE)
    output = re.sub(r"\s+", " ", output).strip()
    output = re.sub(r"\s+([,.;:!?])", r"\1", output)
    output = re.sub(r"\bMas\s+mas\b", "Mas", output, flags=re.IGNORECASE)
    output = re.sub(r"\bMas Como\b", "Como", output)
    output = re.sub(r"\bA Nós\b", "Nós", output)
    output = re.sub(r"\bComo Nós\b", "Como nós", output)
    output = re.sub(r"\bresalte\b", "ressalte", output, flags=re.IGNORECASE)
    output = re.sub(r"\.\s*,", ".", output)
    output = re.sub(r",\s*\.", ".", output)
    output = _capitalize_sentence_starts(output)
    return output


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _capitalize_sentence_starts(text: str) -> str:
    parts = re.split(r"([.!?]\s+)", text)
    output: list[str] = []
    start_next = True
    for part in parts:
        if not part:
            continue
        if re.fullmatch(r"[.!?]\s+", part):
            output.append(part)
            start_next = True
            continue
        if start_next:
            part = re.sub(
                r"^(\W*)([a-záàâãéêíóôõúç])",
                lambda match: f"{match.group(1)}{match.group(2).upper()}",
                part,
            )
        output.append(part)
        start_next = False
    return "".join(output)


def _ensure_terminal_punctuation(text: str) -> str:
    if not text:
        return text
    if text[-1] not in ".!?":
        return f"{text}."
    return text


def looks_truncated(text: str) -> bool:
    cleaned = re.sub(r"\s+", " ", text.strip().lower())
    cleaned = cleaned.rstrip(".!?;:,")
    if not cleaned:
        return False
    if re.fullmatch(r"(como|pois|mas também)", cleaned):
        return True
    if ",." in text:
        return True
    if re.search(r"\b(conveniência e a previsibilidade|lembrar que nossa decisão)\.?$", cleaned):
        return True
    if has_quality_issue(text):
        return True
    if cleaned.endswith("mudanças significativas em preços"):
        return True
    if cleaned.endswith(BAD_ENDINGS):
        return True
    sentence_parts = _split_sentences(text)
    if sentence_parts:
        last_sentence = sentence_parts[-1].strip()
        last_cleaned = re.sub(r"\s+", " ", last_sentence.lower()).rstrip(".!?;:,")
        last_words = re.findall(r"\w+", last_cleaned)
        if re.match(r"^evitar\b", last_cleaned):
            return True
        if 4 <= len(last_words) <= 8 and not _VERB_LIKE_PATTERN.search(last_cleaned):
            return True
    if len(sentence_parts) > 1:
        last_words = re.findall(r"\w+", sentence_parts[-1].lower())
        if 0 < len(last_words) < 4:
            return True
    return bool(
        re.search(
            r"\b(benef|promo|migração|risco:\s*[ao]?|garantir que os produtos|hes|hesitar|tende a ser mais|obstá|também|está|poderia|confort|mud|confian|necess|pre|preço está)$",
            cleaned,
        )
        or bool(re.search(r"\b(man|necess|mainstream|como|pois)$", cleaned))
    )


def has_quality_issue(text: str) -> bool:
    cleaned = re.sub(r"\s+", " ", text.strip().lower())
    if not cleaned:
        return False
    if sum(1 for _ in re.finditer(r"\bisso nos faria\b", cleaned)) > 1:
        return True
    return any(re.search(pattern, cleaned, flags=re.IGNORECASE) for pattern in _QUALITY_ISSUE_PATTERNS)


def normalize_persona_answer(text: str, max_sentences: int = 3, max_words: int = 90) -> str:
    cleaned = _clean_fillers(text)
    sentences = _split_sentences(cleaned)
    if not sentences:
        return ""

    selected: list[str] = []
    word_count = 0
    for sentence in sentences[:max_sentences]:
        if looks_truncated(sentence):
            continue
        words = sentence.split()
        if word_count + len(words) <= max_words:
            selected.append(sentence)
            word_count += len(words)
        else:
            break

    if not selected:
        fallback = sentences[0]
        if looks_truncated(fallback):
            return ""
        words = fallback.split()[:max_words]
        return _ensure_terminal_punctuation(" ".join(words))

    result = " ".join(selected).strip()
    while selected and looks_truncated(result):
        selected.pop()
        result = " ".join(selected).strip()
    return _ensure_terminal_punctuation(result)
