# Codex Implementation Plan — ML Clustering Module

## Project

Repository name:

```text
agentic-customer-intelligence
```

Project description:

```text
End-to-end AI system combining customer clustering, synthetic personas, and multi-agent orchestration for conversational business intelligence.
```

## Context

This project implements the Machine Learning layer of an AI engineering case focused on customer segmentation and synthetic persona generation.

The ML module receives a synthetic consumer dataset, applies preprocessing, feature engineering, dimensionality reduction, clustering, and cluster profiling. The final output is a set of interpretable customer segments that will later be used by an agentic layer, where each cluster becomes a conversational persona.

The goal is not only to run a clustering algorithm, but to build a clear, reproducible, business-oriented ML pipeline that can support downstream AI agents.

## Current Technical Decisions

The repository is organized as a small monorepo:

```text
agentic-customer-intelligence/
├── data/
├── docs/
├── ml-clustering/
├── agentic-personas/
├── apps/
│   ├── api/
│   └── web/
└── infra/
```

Python dependencies are managed with UV from the root `pyproject.toml`.

The ML code lives in:

```text
ml-clustering/src/ml_clustering/
```

This keeps the public module importable as `ml_clustering`, while preserving `ml-clustering` as the business-facing folder name.

The dataset is located at:

```text
data/dados_sinteticos.csv
```

The case PDF is stored under:

```text
docs/Case_Tecnico_ML_AI_Engineer.pdf
```

---

# Objective

Implement the `ml-clustering` module for the `agentic-customer-intelligence` repository.

The ML module must:

1. Load and validate the dataset.
2. Perform initial exploratory data analysis.
3. Engineer features from dates.
4. Treat categorical variables properly.
5. Handle high-cardinality categorical features without creating excessive sparse dimensions.
6. Scale numerical variables.
7. Apply dimensionality reduction for visualization.
8. Test different numbers of clusters.
9. Train a final clustering model.
10. Evaluate clustering quality using internal metrics.
11. Generate cluster profiles.
12. Assign business-friendly segment names.
13. Export outputs for the agentic persona layer.
14. Document the approach clearly.

---

# Input Dataset

The input file is located at:

```text
data/dados_sinteticos.csv
```

Expected columns:

```text
canal_preferido
categoria_favorita
regiao
marca_preferida
influenciador
frequencia_compra
pagamento
genero
ticket_medio
qtd_itens
data_nascimento
```

Expected feature types:

```text
canal_preferido: categorical
categoria_favorita: categorical
regiao: categorical
marca_preferida: high-cardinality categorical
influenciador: high-cardinality categorical
frequencia_compra: ordinal/categorical
pagamento: categorical
genero: categorical
ticket_medio: numerical continuous
qtd_itens: numerical discrete
data_nascimento: date
```

---

# Expected Repository Structure

Create or adjust the repository using the structure below:

```text
agentic-customer-intelligence/
├── data/
│   └── dados_sinteticos.csv
├── ml-clustering/
│   ├── notebooks/
│   │   └── customer_segmentation_clustering.ipynb
│   ├── src/
│   │   └── ml_clustering/
│   │       ├── __init__.py
│   │       ├── paths.py
│   │       ├── data_loader.py
│   │       ├── preprocessing.py
│   │       ├── clustering.py
│   │       ├── profiling.py
│   │       ├── visualization.py
│   │       └── export_outputs.py
│   ├── outputs/
│   │   ├── clustered_consumers.csv
│   │   ├── cluster_summary.csv
│   │   ├── cluster_profiles.json
│   │   ├── cluster_metrics.csv
│   │   └── figures/
│   │       ├── elbow_method.png
│   │       ├── silhouette_scores.png
│   │       ├── clusters_pca_2d.png
│   │       └── clusters_umap_2d.png
│   ├── README.md
│   └── requirements.txt
├── agentic-personas/
│   └── README.md
├── apps/
│   ├── api/
│   └── web/
├── infra/
│   ├── mongodb/
│   └── postgres/
├── docs/
│   ├── Case_Tecnico_ML_AI_Engineer.pdf
│   ├── architecture.md
│   └── executive-summary.md
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── .gitignore
```

---

# Libraries

Use the following libraries:

```text
pandas
numpy
scikit-learn
matplotlib
seaborn
jupyter
```

Optional:

```text
umap-learn
plotly
```

The code must work even if `umap-learn` is not installed. If UMAP is unavailable, skip that visualization and continue with PCA.

---

# Implementation Requirements

## 1. Data Loading and Validation

Create:

```text
ml-clustering/src/ml_clustering/data_loader.py
```

Implement:

```python
load_customer_data(path: str) -> pd.DataFrame
validate_schema(df: pd.DataFrame) -> None
```

Required columns:

```python
REQUIRED_COLUMNS = [
    "canal_preferido",
    "categoria_favorita",
    "regiao",
    "marca_preferida",
    "influenciador",
    "frequencia_compra",
    "pagamento",
    "genero",
    "ticket_medio",
    "qtd_itens",
    "data_nascimento",
]
```

Validation should check:

```text
empty dataset
missing columns
null values
duplicated rows
basic data types
```

For missing required columns, raise a clear error.

For null values and duplicates, print or return a diagnostic summary. Do not necessarily fail unless the issue prevents the pipeline from running.

---

## 2. Initial EDA

In the notebook, create an EDA section with:

```python
df.shape
df.head()
df.info()
df.describe()
df.describe(include="object")
df.isna().sum()
df.nunique().sort_values(ascending=False)
```

Create simple visualizations:

1. Distribution of `ticket_medio`.
2. Distribution of `qtd_itens`.
3. Distribution of `idade`.
4. Count by `canal_preferido`.
5. Count by `categoria_favorita`.
6. Count by `frequencia_compra`.
7. Average ticket by preferred channel.
8. Average ticket by favorite category.

Save important figures in:

```text
ml-clustering/outputs/figures/
```

---

## 3. Feature Engineering

Create:

```text
ml-clustering/src/ml_clustering/preprocessing.py
```

### Date feature

Convert:

```text
data_nascimento -> idade
```

Create:

```text
faixa_etaria
```

Suggested age bands:

```text
18-24
25-34
35-44
45-54
55+
```

Handle invalid dates safely.

### Purchase frequency

Try to map `frequencia_compra` into an ordinal feature when values are clearly ordered.

Suggested mapping:

```python
frequency_order = {
    "baixa": 1,
    "media": 2,
    "média": 2,
    "alta": 3,
    "muito_alta": 4,
    "recorrente": 5,
}
```

Do not assume this mapping will always work. Implement a fallback strategy:

```text
If the values do not match the expected mapping, keep frequencia_compra as categorical and encode it with OneHotEncoder.
```

### High-cardinality categorical variables

Treat the following fields with frequency encoding:

```text
marca_preferida
influenciador
```

Generate:

```text
marca_preferida_freq
influenciador_freq
```

Reasoning to include in the notebook:

```text
High-cardinality categorical variables were encoded using frequency encoding to avoid dimensionality explosion and reduce artificial sparsity introduced by full one-hot encoding.
```

### Low-cardinality categorical variables

Apply OneHotEncoder to:

```text
canal_preferido
categoria_favorita
regiao
pagamento
genero
```

If `frequencia_compra` cannot be mapped reliably to ordinal values, include it in this group as well.

### Numerical variables

Scale numerical features with `StandardScaler`.

Numerical modeling features:

```text
idade
ticket_medio
qtd_itens
marca_preferida_freq
influenciador_freq
frequencia_compra_ord, if available
```

---

## 4. Preprocessing Pipeline

Implement:

```python
build_preprocessing_pipeline(
    numeric_features: list[str],
    categorical_features: list[str]
) -> ColumnTransformer
```

Use:

```text
StandardScaler for numerical features
OneHotEncoder(handle_unknown="ignore") for categorical features
```

Also implement:

```python
prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]
```

Return:

```text
df_model: dataframe with features used for modeling
df_reference: enriched original dataframe used for profiling
```

`df_reference` should include:

```text
idade
faixa_etaria
original categorical variables
original numerical variables
```

---

## 5. Dimensionality Reduction

Create logic in either:

```text
ml-clustering/src/ml_clustering/visualization.py
```

or:

```text
ml-clustering/src/ml_clustering/clustering.py
```

Use PCA for:

1. Reducing transformed features to 2 dimensions.
2. Plotting clusters.
3. Reporting explained variance.

Optionally use UMAP:

```python
try:
    import umap
except ImportError:
    umap = None
```

If UMAP is not installed, skip UMAP without breaking the notebook.

Expected saved figures:

```text
ml-clustering/outputs/figures/clusters_pca_2d.png
ml-clustering/outputs/figures/clusters_umap_2d.png
```

---

## 6. Clustering

Create:

```text
ml-clustering/src/ml_clustering/clustering.py
```

Use KMeans as the main algorithm.

Justification:

```text
KMeans was selected as the main baseline because it is efficient, interpretable, easy to explain to business stakeholders, and suitable for customer segmentation when the main goal is to create actionable and understandable consumer profiles.
```

Test values of `k` from 2 to 8.

For each `k`, calculate:

```text
inertia
silhouette_score
davies_bouldin_score
calinski_harabasz_score
```

Implement:

```python
evaluate_kmeans_k_range(X, k_min=2, k_max=8, random_state=42) -> pd.DataFrame
fit_final_kmeans(X, n_clusters: int, random_state=42) -> KMeans
```

Use:

```python
RANDOM_STATE = 42
```

---

## 7. Choosing the Number of Clusters

The final `k` should be selected based on:

```text
internal metrics
elbow curve
silhouette score
business interpretability
manageable number of personas for stakeholders
```

Prefer a value between 3 and 5 unless the metrics strongly suggest otherwise.

Include this explanation in the notebook:

```text
The final number of clusters was not selected based on a single metric only. For customer segmentation, it is important to balance statistical quality, visual separation, and executive interpretability. A segmentation with too many clusters can be difficult for business users to understand and can also make the downstream agentic persona layer harder to use. Therefore, the final choice considers both internal clustering metrics and the ability to translate clusters into actionable personas.
```

---

## 8. Cluster Profiling

Create:

```text
ml-clustering/src/ml_clustering/profiling.py
```

Implement:

```python
build_cluster_summary(df_with_clusters: pd.DataFrame) -> pd.DataFrame
```

The output table should include:

```text
cluster
segment_name
cluster_size
cluster_share
idade_media
ticket_medio_medio
qtd_itens_medio
canal_preferido_modal
categoria_favorita_modal
regiao_modal
marca_preferida_modal
influenciador_modal
frequencia_compra_modal
pagamento_modal
genero_modal
faixa_etaria_modal
```

Also implement:

```python
get_top_categories_by_cluster(
    df: pd.DataFrame,
    cluster_col: str,
    categorical_cols: list[str],
    top_n: int = 3
) -> dict
```

This function should return the most frequent categorical values by cluster.

---

## 9. Segment Naming

Implement:

```python
assign_segment_names(cluster_summary: pd.DataFrame) -> pd.DataFrame
```

Do not leave the final output as only:

```text
Cluster 0
Cluster 1
Cluster 2
```

Create business-friendly names based on the dominant cluster profile.

Examples:

```text
Jovens Digitais de Alta Frequência
Consumidores Premium Recorrentes
Compradores Econômicos de Loja Física
Famílias Regionais Sensíveis à Conveniência
Consumidores Influenciados por Marca
Clientes Omnichannel de Ticket Médio
```

The naming logic can combine:

```text
dominant age band
preferred channel
favorite category
average ticket
purchase frequency
```

It does not need to be perfect, but it must be explainable.

---

## 10. Business Interpretation

Implement:

```python
generate_business_interpretation(row: pd.Series) -> str
```

For each cluster, generate a concise business interpretation.

Example:

```text
Segment with above-average ticket, preference for digital channels, and high purchase frequency. This group may respond well to loyalty programs, personalized offers, and premium experiences.
```

Also implement:

```python
generate_agent_persona_prompt(row: pd.Series) -> str
```

The persona prompt must be derived from the cluster profile.

Example format:

```text
You represent a consumer segment called "{segment_name}".

Statistical characteristics of this segment:
- Average age: {idade_media}
- Dominant age range: {faixa_etaria_modal}
- Preferred channel: {canal_preferido_modal}
- Favorite category: {categoria_favorita_modal}
- Dominant region: {regiao_modal}
- Dominant purchase frequency: {frequencia_compra_modal}
- Dominant payment method: {pagamento_modal}
- Average ticket: R$ {ticket_medio_medio}
- Average number of items: {qtd_itens_medio}

Expected behavior:
{business_interpretation}

Instructions:
Always answer in first person, as a typical consumer from this segment.
If asked about price, channel, product, brand, or promotion, answer based on the profile above.
Do not invent new statistical data.
When uncertain, answer qualitatively and consistently with the segment profile.
```

This is important because the downstream agentic layer must instantiate agents procedurally from ML outputs.

---

## 11. Output Export

Create:

```text
ml-clustering/src/ml_clustering/export_outputs.py
```

Generate:

```text
ml-clustering/outputs/clustered_consumers.csv
ml-clustering/outputs/cluster_summary.csv
ml-clustering/outputs/cluster_profiles.json
ml-clustering/outputs/cluster_metrics.csv
```

Expected `cluster_profiles.json` format:

```json
[
  {
    "cluster_id": 0,
    "segment_name": "Jovens Digitais de Alta Frequência",
    "cluster_size": 520,
    "cluster_share": 0.1733,
    "profile": {
      "idade_media": 27.4,
      "faixa_etaria_modal": "25-34",
      "ticket_medio_medio": 84.2,
      "qtd_itens_medio": 4.8,
      "canal_preferido_modal": "app",
      "categoria_favorita_modal": "snacks",
      "regiao_modal": "sudeste",
      "marca_preferida_modal": "marca_x",
      "influenciador_modal": "influenciador_y",
      "frequencia_compra_modal": "alta",
      "pagamento_modal": "cartao_credito",
      "genero_modal": "feminino"
    },
    "business_interpretation": "Segmento jovem, digital e recorrente, com preferência por compras via app e categorias de conveniência.",
    "persona_prompt": "..."
  }
]
```

---

## 12. Notebook

Create:

```text
ml-clustering/notebooks/customer_segmentation_clustering.ipynb
```

Notebook structure:

```text
1. Business Context
2. Dataset Overview
3. Initial EDA
4. Data Quality Checks
5. Feature Engineering
6. Categorical Encoding Strategy
7. Preprocessing Pipeline
8. Dimensionality Reduction
9. Clustering Model Selection
10. Internal Metrics
11. Final Clustering
12. Cluster Visualization
13. Cluster Profiling
14. Business Interpretation
15. Export for Agentic Layer
16. Limitations and Next Steps
```

Use Markdown explanations between code cells.

The notebook should be readable as a technical report, not only as executable code.

---

## 13. ML README

Create:

```text
ml-clustering/README.md
```

Suggested content:

```markdown
# Customer Segmentation ML Pipeline

## Objective

This module clusters consumers using unsupervised learning and exports interpretable segment profiles for the agentic persona layer.

## Dataset

The dataset contains demographic, behavioral, survey-like, and purchase-related consumer attributes.

## Approach

- Data validation
- Feature engineering
- Categorical encoding
- Numerical scaling
- Dimensionality reduction
- KMeans clustering
- Internal clustering metrics
- Cluster profiling
- Export to JSON for persona agents

## Why KMeans

KMeans was selected as the main clustering algorithm because it is efficient, interpretable, and suitable for business-oriented customer segmentation.

## How to Run

```bash
uv sync
uv run jupyter notebook ml-clustering/notebooks/customer_segmentation_clustering.ipynb
```

## Outputs

- `clustered_consumers.csv`: original consumers with assigned cluster labels.
- `cluster_summary.csv`: business-readable summary of each cluster.
- `cluster_profiles.json`: structured segment profiles and persona prompts for the agentic layer.
- `cluster_metrics.csv`: internal metrics for different values of k.

## Connection with Agentic Layer

The `cluster_profiles.json` file is consumed by the Streamlit multi-agent application. Each cluster profile becomes a synthetic persona agent that can answer business questions conversationally.

## Limitations

- The dataset is synthetic.
- Clusters are statistical approximations, not absolute consumer truths.
- Personas should not be treated as real individuals.
- Results depend on feature engineering and encoding choices.
- A production system would require business validation and monitoring for data drift.
```

---

## 14. Root README

Create or update:

```text
README.md
```

Suggested content:

```markdown
# Agentic Customer Intelligence

End-to-end AI system combining customer clustering, synthetic personas, and multi-agent orchestration for conversational business intelligence.

## Modules

### ml-clustering

Builds consumer segments using unsupervised learning and exports cluster profiles.

### agentic-personas

Uses the generated cluster profiles to instantiate persona agents that answer business questions conversationally.

## End-to-End Flow

```text
Raw customer data
→ ML preprocessing
→ clustering
→ cluster profiling
→ persona prompt generation
→ multi-agent conversational interface
```

## Current Status

- ML pipeline implemented
- Cluster profiles exported
- Agentic layer planned or implemented separately
```

---

## 15. Code Quality Requirements

The implementation must use:

```text
small functions
clear names
simple comments where useful
relative paths
fixed random state
minimal hardcoding
basic error handling
reproducible outputs
```

Use:

```python
RANDOM_STATE = 42
```

Avoid duplicated logic.

---

## 16. Acceptance Criteria

The implementation is complete when:

```text
The notebook runs end-to-end
The dataset is loaded correctly
The schema is validated
Age is created from birth date
Age bands are created
High-cardinality categorical features are handled without full OneHot
Low-cardinality categorical features are encoded properly
Numerical features are scaled
KMeans is evaluated from k=2 to k=8
Internal metrics are calculated
Elbow and silhouette charts are generated
Final clusters are assigned to all consumers
Cluster profiles are generated
Each cluster receives a business-friendly name
clustered_consumers.csv is exported
cluster_summary.csv is exported
cluster_profiles.json is exported
cluster_metrics.csv is exported
The ML README explains how to run the module
The root README explains the end-to-end project
```

---

## 17. Delivery Style

The final result should look like work from a senior AI Engineer:

```text
pragmatic
simple
explainable
reproducible
business-oriented
ready to integrate with the agentic layer
```

Do not overengineer.

Focus on clarity, explainability, and the bridge between ML segmentation and agentic personas.
