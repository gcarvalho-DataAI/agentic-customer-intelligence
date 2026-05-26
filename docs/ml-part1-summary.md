# Parte 1 - Resumo Executivo de ML

## Quantidade de clusters

Foram identificados **3 segmentos** de consumidores (`k=3`), escolhidos com base em métricas internas (silhouette, davies-bouldin, calinski-harabasz), curva de elbow e interpretabilidade para uso de negócio.

## Perfis principais

1. **Consumidores Maduros do Norte com Pagamento Digital**
   - Participação: 35.2%
   - Idade média: 58.2 anos
   - Ticket médio: R$ 120.45
   - Traços: canal `loja_fisica`, categoria `bebidas`, frequência `semanal` e região `norte`.
   - Diferencial principal: faixa etária '55+' acima da base (66.3% vs 32.1%)

1. **Jovens Adultos Recorrentes do Sudeste**
   - Participação: 34.2%
   - Idade média: 30.0 anos
   - Ticket médio: R$ 123.36
   - Traços: canal `loja_fisica`, categoria `bebidas`, frequência `semanal` e região `sudeste`.
   - Diferencial principal: idade média abaixo da base (30.0 vs 44.6)

1. **Consumidores Mainstream Recorrentes do Sudeste**
   - Participação: 30.6%
   - Idade média: 45.4 anos
   - Ticket médio: R$ 121.66
   - Traços: canal `loja_fisica`, categoria `bebidas`, frequência `semanal` e região `sudeste`.
   - Diferencial principal: quantidade média de itens acima da base (4.2 vs 4.0)

## Aplicações para negócio

1. Ajustar campanhas por faixa etária e região, mantendo linguagem e canal de ativação aderentes ao comportamento de compra.
2. Personalizar ofertas por método de pagamento predominante para elevar conversão sem reduzir margem.
3. Usar os perfis como base de personas sintéticas para simular decisões comerciais (preço, promoções e canais).

## Observações de qualidade analítica

- A base é sintética e tende a concentrar modas categóricas, o que pode reduzir separação semântica entre clusters.
- A segmentação deve ser tratada como base de hipótese e priorização, com validação adicional em contexto real de negócio.
- O cluster mainstream tem menor diferenciação estatística e deve ser apresentado como segmento de transição ou grupo próximo da média da base.
