# Comparativo de Estratégias de Clusterização

Tabela consolidada em `ml-clustering/outputs/strategy_comparison.csv`.

## Melhores resultados por métrica

- Melhor silhouette: `kmeans_auto_silhouette` com `k=2` (0.0754)
- Melhor Davies-Bouldin (menor): `dbscan` com `k=-1` (1.5540)
- Melhor Calinski-Harabasz: `kmeans_auto_silhouette` com `k=2` (253.69)

## Leitura para decisão

- `k=4` e `k=5` aumentam granularidade, mas tendem a reduzir silhouette no KMeans em relação a `k=3`.
- Estratégias alternativas (GMM/Agglomerative) podem melhorar algumas métricas, mas exigem mais explicação para stakeholders.
- DBSCAN depende bastante de `eps` e `min_samples`; quando calibrado, pode revelar estrutura não esférica, mas tende a produzir ruído.
- KMedoids é mais robusto a outliers do que KMeans, porém pode perder desempenho em separação global neste dataset.
- Para o case, KMeans com `k=3` ou `k=4` costuma ser o melhor equilíbrio entre interpretabilidade e qualidade.
