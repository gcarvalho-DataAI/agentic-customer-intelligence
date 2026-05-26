# Customer Segmentation ML Pipeline

This module contains the Machine Learning part of the case: customer segmentation through clustering and export of cluster profiles for the agentic persona layer.

## Dataset

The input dataset is expected at:

```text
data/dados_sinteticos.csv
```

## Approach

- Validate schema and data quality.
- Create date-derived features such as age and age band.
- Encode high-cardinality categorical variables with frequency encoding.
- Encode low-cardinality categorical variables with one-hot encoding.
- Scale numerical variables.
- Evaluate KMeans with multiple values of `k`.
- Use internal metrics and business interpretability to choose the final clustering.
- Generate cluster summaries, business interpretations, and persona prompts.

## Outputs

Generated artifacts will be written to:

```text
ml-clustering/outputs/
```

Expected files:

- `clustered_consumers.csv`
- `cluster_summary.csv`
- `cluster_profiles.json`
- `cluster_metrics.csv`
- `figures/*.png`

## Run

```bash
uv sync
PYTHONPATH=ml-clustering/src uv run python ml-clustering/run_pipeline.py
PYTHONPATH=ml-clustering/src uv run python ml-clustering/generate_part1_summary.py
uv run jupyter notebook ml-clustering/notebooks/customer_segmentation_clustering.ipynb
```
