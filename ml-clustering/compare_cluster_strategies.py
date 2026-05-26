from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.mixture import GaussianMixture

from ml_clustering.clustering import RANDOM_STATE, choose_k, evaluate_kmeans_k_range
from ml_clustering.data_loader import load_customer_data, validate_schema
from ml_clustering.paths import DATA_PATH, OUTPUTS_DIR, PROJECT_ROOT
from ml_clustering.preprocessing import build_preprocessing_pipeline, prepare_features

try:
    from kmedoids import KMedoids
except Exception:
    KMedoids = None


def _balance_stats(labels: np.ndarray) -> tuple[float, float]:
    shares = pd.Series(labels).value_counts(normalize=True)
    return float(shares.min()), float(shares.max())


def _evaluate_labels(x: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    unique_labels = np.unique(labels)
    if len(unique_labels) < 2:
        return {
            "silhouette_score": np.nan,
            "davies_bouldin_score": np.nan,
            "calinski_harabasz_score": np.nan,
            "min_cluster_share": np.nan,
            "max_cluster_share": np.nan,
            "noise_share": np.nan,
            "n_clusters_found": float(len(unique_labels)),
        }

    min_share, max_share = _balance_stats(labels)
    noise_share = float(np.mean(labels == -1)) if (-1 in unique_labels) else 0.0
    return {
        "silhouette_score": float(silhouette_score(x, labels)),
        "davies_bouldin_score": float(davies_bouldin_score(x, labels)),
        "calinski_harabasz_score": float(calinski_harabasz_score(x, labels)),
        "min_cluster_share": min_share,
        "max_cluster_share": max_share,
        "noise_share": noise_share,
        "n_clusters_found": float(len([lbl for lbl in unique_labels if lbl != -1])),
    }


def _run_kmeans(x: np.ndarray, k: int) -> dict[str, float | int | str]:
    model = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=20)
    labels = model.fit_predict(x)
    row: dict[str, float | int | str] = {"strategy": "kmeans_fixed", "k": k, "inertia": float(model.inertia_)}
    row.update(_evaluate_labels(x, labels))
    return row


def _run_gmm(x: np.ndarray, k: int) -> dict[str, float | int | str]:
    model = GaussianMixture(n_components=k, random_state=RANDOM_STATE)
    labels = model.fit_predict(x)
    row: dict[str, float | int | str] = {"strategy": "gmm_fixed", "k": k, "inertia": np.nan}
    row.update(_evaluate_labels(x, labels))
    return row


def _run_agglomerative(x: np.ndarray, k: int) -> dict[str, float | int | str]:
    model = AgglomerativeClustering(n_clusters=k, linkage="ward")
    labels = model.fit_predict(x)
    row: dict[str, float | int | str] = {"strategy": "agglomerative_fixed", "k": k, "inertia": np.nan}
    row.update(_evaluate_labels(x, labels))
    return row


def _run_kmedoids(x: np.ndarray, k: int) -> dict[str, float | int | str]:
    if KMedoids is None:
        return {
            "strategy": "kmedoids_fixed",
            "k": k,
            "inertia": np.nan,
            "silhouette_score": np.nan,
            "davies_bouldin_score": np.nan,
            "calinski_harabasz_score": np.nan,
            "min_cluster_share": np.nan,
            "max_cluster_share": np.nan,
            "noise_share": np.nan,
            "n_clusters_found": np.nan,
            "notes": "kmedoids_not_available",
        }
    try:
        model = KMedoids(
            n_clusters=k,
            random_state=RANDOM_STATE,
            method="fasterpam",
            metric="euclidean",
        )
        labels = model.fit_predict(x)
        inertia = getattr(model, "inertia_", np.nan)
        row: dict[str, float | int | str] = {
            "strategy": "kmedoids_fixed",
            "k": k,
            "inertia": float(inertia),
        }
        row.update(_evaluate_labels(x, labels))
        return row
    except BaseException as exc:
        return {
            "strategy": "kmedoids_fixed",
            "k": k,
            "inertia": np.nan,
            "silhouette_score": np.nan,
            "davies_bouldin_score": np.nan,
            "calinski_harabasz_score": np.nan,
            "min_cluster_share": np.nan,
            "max_cluster_share": np.nan,
            "noise_share": np.nan,
            "n_clusters_found": np.nan,
            "notes": f"kmedoids_error:{type(exc).__name__}",
        }


def _run_dbscan(
    x: np.ndarray,
    eps: float,
    min_samples: int,
    metric: str = "euclidean",
) -> dict[str, float | int | str]:
    model = DBSCAN(eps=eps, min_samples=min_samples, metric=metric)
    labels = model.fit_predict(x)
    row: dict[str, float | int | str] = {
        "strategy": "dbscan",
        "k": -1,
        "inertia": np.nan,
        "eps": eps,
        "min_samples": min_samples,
        "distance_metric": metric,
    }
    row.update(_evaluate_labels(x, labels))
    return row


def _build_markdown_report(df: pd.DataFrame) -> str:
    valid = df[df["silhouette_score"].notna()].copy()
    best_silhouette = valid.sort_values("silhouette_score", ascending=False).iloc[0]
    best_db = valid.sort_values("davies_bouldin_score", ascending=True).iloc[0]
    best_ch = valid.sort_values("calinski_harabasz_score", ascending=False).iloc[0]

    lines: list[str] = []
    lines.append("# Comparativo de Estratégias de Clusterização")
    lines.append("")
    lines.append("Tabela consolidada em `ml-clustering/outputs/strategy_comparison.csv`.")
    lines.append("")
    lines.append("## Melhores resultados por métrica")
    lines.append("")
    lines.append(
        f"- Melhor silhouette: `{best_silhouette['strategy']}` com `k={int(best_silhouette['k'])}` "
        f"({best_silhouette['silhouette_score']:.4f})"
    )
    lines.append(
        f"- Melhor Davies-Bouldin (menor): `{best_db['strategy']}` com `k={int(best_db['k'])}` "
        f"({best_db['davies_bouldin_score']:.4f})"
    )
    lines.append(
        f"- Melhor Calinski-Harabasz: `{best_ch['strategy']}` com `k={int(best_ch['k'])}` "
        f"({best_ch['calinski_harabasz_score']:.2f})"
    )
    lines.append("")
    lines.append("## Leitura para decisão")
    lines.append("")
    lines.append(
        "- `k=4` e `k=5` aumentam granularidade, mas tendem a reduzir silhouette no KMeans em relação a `k=3`."
    )
    lines.append(
        "- Estratégias alternativas (GMM/Agglomerative) podem melhorar algumas métricas, mas exigem mais explicação para stakeholders."
    )
    if "dbscan" in set(df["strategy"]):
        lines.append(
            "- DBSCAN depende bastante de `eps` e `min_samples`; quando calibrado, pode revelar estrutura não esférica, mas tende a produzir ruído."
        )
    if "kmedoids_fixed" in set(df["strategy"]):
        lines.append(
            "- KMedoids é mais robusto a outliers do que KMeans, porém pode perder desempenho em separação global neste dataset."
        )
    lines.append(
        "- Para o case, KMeans com `k=3` ou `k=4` costuma ser o melhor equilíbrio entre interpretabilidade e qualidade."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    df = load_customer_data(DATA_PATH)
    validate_schema(df)
    df_model, _, numeric_features, categorical_features = prepare_features(df)
    preprocessor = build_preprocessing_pipeline(numeric_features, categorical_features)
    x = preprocessor.fit_transform(df_model)

    rows: list[dict[str, float | int | str]] = []

    metrics_range = evaluate_kmeans_k_range(x, k_min=2, k_max=8)
    auto_k_business = choose_k(metrics_range, preferred_min=3, preferred_max=5)
    auto_k_silhouette = int(metrics_range.sort_values("silhouette_score", ascending=False).iloc[0]["k"])

    auto_business_row = _run_kmeans(x, auto_k_business)
    auto_business_row["strategy"] = "kmeans_auto_business"
    rows.append(auto_business_row)

    auto_silhouette_row = _run_kmeans(x, auto_k_silhouette)
    auto_silhouette_row["strategy"] = "kmeans_auto_silhouette"
    rows.append(auto_silhouette_row)

    for k in [3, 4, 5]:
        rows.append(_run_kmeans(x, k))
        rows.append(_run_kmedoids(x, k))
        rows.append(_run_gmm(x, k))
        rows.append(_run_agglomerative(x, k))
    for metric in ["euclidean", "cosine"]:
        for eps in [0.2, 0.35, 0.5, 0.8, 1.0, 1.2, 1.5]:
            for min_samples in [3, 5, 10, 20]:
                rows.append(_run_dbscan(x, eps=eps, min_samples=min_samples, metric=metric))

    comparison = pd.DataFrame(rows)
    if "notes" not in comparison.columns:
        comparison["notes"] = ""
    if "eps" not in comparison.columns:
        comparison["eps"] = np.nan
    if "min_samples" not in comparison.columns:
        comparison["min_samples"] = np.nan
    if "distance_metric" not in comparison.columns:
        comparison["distance_metric"] = ""
    comparison = comparison[
        [
            "strategy",
            "k",
            "distance_metric",
            "eps",
            "min_samples",
            "silhouette_score",
            "davies_bouldin_score",
            "calinski_harabasz_score",
            "n_clusters_found",
            "noise_share",
            "min_cluster_share",
            "max_cluster_share",
            "inertia",
            "notes",
        ]
    ].copy()
    comparison.sort_values(["strategy", "k", "distance_metric", "eps", "min_samples"], inplace=True)

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    comparison_path = OUTPUTS_DIR / "strategy_comparison.csv"
    comparison.to_csv(comparison_path, index=False)

    report_path = PROJECT_ROOT / "docs" / "ml-strategy-comparison.md"
    report_path.write_text(_build_markdown_report(comparison), encoding="utf-8")

    print(f"Saved: {comparison_path}")
    print(f"Saved: {report_path}")


if __name__ == "__main__":
    main()
