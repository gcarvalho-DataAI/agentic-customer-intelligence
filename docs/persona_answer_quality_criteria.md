# Persona Answer Quality Criteria

Este documento define como avaliar as respostas dos agentes-persona do ponto de vista de produto, marketing, ML e agentic AI. O objetivo não é apenas gerar respostas bonitas, mas demonstrar que o sistema funciona como uma solução real de inteligência de marketing.

## 1. Diferenciacao Entre Personas

Este é o critério principal. Cada persona precisa responder de um jeito claramente diferente.

Sinais esperados:

- Persona 0: carteira digital, cashback, loja física, confiança, disponibilidade, baixa fricção no pagamento.
- Persona 1: crédito, pontos, comunicação digital pré-compra, conveniência, controle financeiro.
- Persona 2: cautela, previsibilidade, estabilidade, benefício recorrente, mudança gradual.

Se as três respostas puderem ser copiadas e coladas entre cards com pouca mudança, o sistema está fraco.

## 2. Aderencia Ao Perfil Estatistico

A resposta deve respeitar o que veio do cluster.

- Se o canal preferido é `loja_fisica`, a persona não deve soar digital-first.
- Se o pagamento dominante é `credito`, faz sentido falar de pontos, cartão e benefícios financeiros.
- Se o pagamento dominante é `carteira_digital`, faz sentido falar de cashback, desconto instantâneo e pagamento simples.

## 3. Uso Dos Diferenciais Contra A Base

Uma resposta boa não usa apenas a moda do cluster. Ela usa aquilo que torna o cluster diferente da base geral.

Exemplo forte:

> Como este grupo tem carteira digital acima da base, cashback e desconto instantâneo são bons gatilhos.

Exemplo fraco:

> Gostamos de promoções.

## 4. Naturalidade Da Resposta

A resposta deve parecer conversacional e útil para produto/marketing, não um relatório estatístico.

Evitar:

- `é importante considerar`
- `é importante notar`
- `o que sugere que`
- `pode indicar que`

Preferir:

- `Nós trocaríamos se...`
- `Para nós, o principal gatilho seria...`
- `A troca precisa parecer...`

## 5. Utilidade Para Marketing

A resposta precisa gerar ação. Ela deve ajudar um time de marketing a decidir:

- qual promoção testar
- qual canal usar
- qual mensagem comunicar
- qual risco reduzir
- qual benefício destacar

Resposta fraca:

> Nós gostamos de benefícios.

Resposta forte:

> Uma campanha no ponto de venda com "pague com carteira digital e ganhe desconto agora" tende a ser mais adequada para este segmento.

## 6. Clareza E Concisao

Para cards lado a lado, a resposta precisa ser curta.

Critério ideal:

- 3 frases
- até 90 palavras
- sem rodeios
- sem explicação técnica longa

Se a resposta vira um parágrafo grande, a comparação visual perde força.

## 7. Coerencia Com O RAG

O contexto recuperado deve aparecer na resposta sem dominar.

Ordem de prioridade:

1. Cluster profile manda.
2. RAG enriquece.
3. Guardrails controlam.

Se todas as personas usam o mesmo conteúdo compartilhado, o RAG está atrapalhando. Se cada persona usa documentos específicos e fica mais diferenciada, o RAG está ajudando.

## 8. Cuidado Com Overclaim

A persona não deve afirmar coisas que os dados não sustentam.

Evitar:

- `Esse público sempre troca por cashback.`
- `Esse público é fiel.`
- `Esse público não gosta de digital.`

Preferir:

- `Esse perfil tende a responder melhor a cashback.`
- `A troca parece depender de confiança e benefício claro.`
- `A migração para digital exigiria baixo atrito.`

## 9. Tratamento De Incerteza

Especialmente para a Persona 2, que tem menor diferenciação, a resposta deve ser mais cautelosa.

Boa resposta:

> Como este segmento é mais mainstream, a troca tende a ser gradual e depende de consistência.

Resposta ruim:

> Esse segmento com certeza troca por preço.

## 10. Comparabilidade Na Interface

As respostas devem ter estrutura parecida, mas conteúdo diferente.

Estrutura recomendada:

- gatilho principal
- benefício mais forte
- barreira ou risco

Exemplos:

- Persona 0: gatilho = cashback no caixa; barreira = fricção no pagamento.
- Persona 1: gatilho = pontos/crédito; barreira = pouca conveniência.
- Persona 2: gatilho = preço estável; barreira = mudança brusca.

## Score Mental

Cada resposta deve ser avaliada de 0 a 5 em:

- Diferenciação entre personas
- Aderência ao cluster
- Utilidade para marketing
- Naturalidade
- Concisão
- Cautela/guardrails

Meta para demo:

- média geral >= 4.0
- nenhum critério crítico abaixo de 3.5
- respostas sem truncamento
- respostas comparáveis nos cards

