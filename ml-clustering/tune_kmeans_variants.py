from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import Normalizer

from ml_clustering.clustering import RANDOM_STATE
from ml_clustering.data_loader import load_customer_data, validate_schema
from ml_clustering.paths import DATA_PATH, OUTPUTS_DIR
from ml_clustering.preprocessing import build_preprocessing_pipeline, prepare_features


def _eval(labels: np.ndarray, x: np.ndarray) -> dict[str, float]:
    return {
        "silhouette_score": float(silhouette_score(x, labels)),
        "davies_bouldin_score": float(davies_bouldin_score(x, labels)),
        "calinski_harabasz_score": float(calinski_harabasz_score(x, labels)),
    }


def _run_kmeans(x: np.ndarray, k: int) -> dict[str, float]:
    model = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=50, init="k-means++")
    labels = model.fit_predict(x)
    metrics = _eval(labels, x)
    metrics["inertia"] = float(model.inertia_)
    return metrics


def main() -> None:
    df = load_customer_data(DATA_PATH)
    validate_schema(df)
    df_model, _, numeric_features, categorical_features = prepare_features(df)
    pre = build_preprocessing_pipeline(numeric_features, categorical_features)
    x = pre.fit_transform(df_model)

    # Build candidates that usually help mixed sparse features.
    candidates: list[tuple[str, Pipeline | None]] = [
        ("baseline_raw", None),
        ("svd30", Pipeline([("svd", TruncatedSVD(n_components=30, random_state=RANDOM_STATE))])),
        ("svd50", Pipeline([("svd", TruncatedSVD(n_components=50, random_state=RANDOM_STATE))])),
        (
            "svd50_l2norm",
            Pipeline(
                [
                    ("svd", TruncatedSVD(n_components=50, random_state=RANDOM_STATE)),
                    ("norm", Normalizer(norm="l2")),
                ]
            ),
        ),
        ("pca20_dense", Pipeline([("pca", PCA(n_components=20, random_state=RANDOM_STATE))])),
    ]

    rows: list[dict[str, float | int | str]] = []
    for name, transform in candidates:
        try:
            xt = x if transform is None else transform.fit_transform(x)
            for k in [3, 4, 5]:
                metrics = _run_kmeans(xt, k)
                rows.append({"variant": name, "k": k, **metrics})
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {
                    "variant": name,
                    "k": -1,
                    "silhouette_score": np.nan,
                    "davies_bouldin_score": np.nan,
                    "calinski_harabasz_score": np.nan,
                    "inertia": np.nan,
                    "error": type(exc).__name__,
                }
            )

    out = pd.DataFrame(rows)
    if "error" not in out.columns:
        out["error"] = ""

    out = out[
        [
            "variant",
            "k",
            "silhouette_score",
            "davies_bouldin_score",
            "calinski_harabasz_score",
            "inertia",
            "error",
        ]
    ].sort_values(["silhouette_score", "davies_bouldin_score"], ascending=[False, True])

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUTS_DIR / "kmeans_variants_comparison.csv"
    out.to_csv(out_path, index=False)

    best = out[out["k"] > 0].iloc[0]
    print(f"Saved: {out_path}")
    print(
        "Best variant: "
        f"{best['variant']} (k={int(best['k'])}) "
        f"sil={best['silhouette_score']:.4f} "
        f"db={best['davies_bouldin_score']:.4f} "
        f"ch={best['calinski_harabasz_score']:.2f}"
    )


if __name__ == "__main__":
    main()

