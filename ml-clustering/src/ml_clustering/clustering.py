from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

RANDOM_STATE = 42
KMEANS_N_INIT = 50


def build_modeling_matrix(
    x,
    strategy: str = "pca20",
    random_state: int = RANDOM_STATE,
) -> tuple[np.ndarray, dict[str, float | int | str]]:
    if strategy == "raw":
        arr = x.toarray() if sparse.issparse(x) else np.asarray(x)
        return arr, {"modeling_strategy": "raw", "modeling_components": arr.shape[1]}

    if strategy == "pca20":
        if sparse.issparse(x):
            svd = TruncatedSVD(n_components=20, random_state=random_state)
            arr = svd.fit_transform(x)
            explained = float(np.sum(svd.explained_variance_ratio_))
            return arr, {
                "modeling_strategy": "truncated_svd_20",
                "modeling_components": 20,
                "explained_variance": explained,
            }

        pca = PCA(n_components=20, random_state=random_state)
        arr = pca.fit_transform(x)
        explained = float(np.sum(pca.explained_variance_ratio_))
        return arr, {
            "modeling_strategy": "pca_20",
            "modeling_components": 20,
            "explained_variance": explained,
        }

    raise ValueError(f"Unknown modeling strategy: {strategy}")


def evaluate_kmeans_k_range(
    x: np.ndarray,
    k_min: int = 2,
    k_max: int = 8,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    rows: list[dict[str, float | int]] = []
    for k in range(k_min, k_max + 1):
        model = KMeans(n_clusters=k, random_state=random_state, n_init=KMEANS_N_INIT)
        labels = model.fit_predict(x)
        rows.append(
            {
                "k": k,
                "inertia": float(model.inertia_),
                "silhouette_score": float(silhouette_score(x, labels)),
                "davies_bouldin_score": float(davies_bouldin_score(x, labels)),
                "calinski_harabasz_score": float(calinski_harabasz_score(x, labels)),
            }
        )
    return pd.DataFrame(rows)


def choose_k(metrics_df: pd.DataFrame, preferred_min: int = 3, preferred_max: int = 5) -> int:
    within_band = metrics_df[(metrics_df["k"] >= preferred_min) & (metrics_df["k"] <= preferred_max)].copy()
    target = within_band if not within_band.empty else metrics_df.copy()

    sil_best = int(target.sort_values("silhouette_score", ascending=False).iloc[0]["k"])
    db_best = int(target.sort_values("davies_bouldin_score", ascending=True).iloc[0]["k"])
    ch_best = int(target.sort_values("calinski_harabasz_score", ascending=False).iloc[0]["k"])

    votes = pd.Series([sil_best, db_best, ch_best]).value_counts()
    return int(votes.index[0])


def fit_final_kmeans(x: np.ndarray, n_clusters: int, random_state: int = RANDOM_STATE) -> KMeans:
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=KMEANS_N_INIT)
    model.fit(x)
    return model


def project_pca_2d(x: np.ndarray, random_state: int = RANDOM_STATE) -> tuple[np.ndarray, float]:
    pca = PCA(n_components=2, random_state=random_state)
    coords = pca.fit_transform(x)
    explained = float(np.sum(pca.explained_variance_ratio_))
    return coords, explained


def project_umap_2d(x: np.ndarray, random_state: int = RANDOM_STATE) -> np.ndarray | None:
    try:
        import umap
    except ImportError:
        return None
    reducer = umap.UMAP(n_components=2, random_state=random_state)
    return reducer.fit_transform(x)
