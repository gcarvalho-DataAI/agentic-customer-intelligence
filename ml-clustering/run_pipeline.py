from __future__ import annotations

from pathlib import Path

from ml_clustering.clustering import (
    build_modeling_matrix,
    choose_k,
    evaluate_kmeans_k_range,
    fit_final_kmeans,
    project_pca_2d,
    project_umap_2d,
)
from ml_clustering.data_loader import load_customer_data, validate_schema
from ml_clustering.export_outputs import (
    export_cluster_metrics,
    export_cluster_profiles_json,
    export_cluster_summary,
    export_clustered_consumers,
)
from ml_clustering.paths import DATA_PATH, FIGURES_DIR, OUTPUTS_DIR
from ml_clustering.preprocessing import build_preprocessing_pipeline, prepare_features
from ml_clustering.profiling import (
    add_cluster_differentiators,
    assign_segment_names,
    build_cluster_summary,
)
from ml_clustering.visualization import plot_2d_clusters, plot_kmeans_metrics


def main() -> None:
    df = load_customer_data(DATA_PATH)
    diagnostics = validate_schema(df)
    print(f"Loaded dataset: {diagnostics['row_count']} rows, {diagnostics['column_count']} columns")

    df_model, df_reference, numeric_features, categorical_features = prepare_features(df)
    preprocessor = build_preprocessing_pipeline(
        numeric_features=numeric_features,
        categorical_features=categorical_features,
    )
    x = preprocessor.fit_transform(df_model)
    x_model, modeling_info = build_modeling_matrix(x, strategy="pca20")
    print(
        "Modeling matrix:",
        modeling_info["modeling_strategy"],
        f"components={modeling_info['modeling_components']}",
    )

    metrics = evaluate_kmeans_k_range(x_model, k_min=2, k_max=8)
    selected_k = choose_k(metrics, preferred_min=3, preferred_max=5)
    model = fit_final_kmeans(x_model, n_clusters=selected_k)
    labels = model.labels_

    df_with_clusters = df_reference.copy()
    df_with_clusters["cluster"] = labels

    summary = build_cluster_summary(df_with_clusters)
    summary = assign_segment_names(summary)
    summary = add_cluster_differentiators(df_with_clusters, summary)
    summary = summary.sort_values("cluster").reset_index(drop=True)

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    export_clustered_consumers(df_with_clusters, OUTPUTS_DIR / "clustered_consumers.csv")
    export_cluster_summary(summary, OUTPUTS_DIR / "cluster_summary.csv")
    export_cluster_profiles_json(summary, OUTPUTS_DIR / "cluster_profiles.json")
    export_cluster_metrics(metrics, OUTPUTS_DIR / "cluster_metrics.csv")

    plot_kmeans_metrics(metrics, FIGURES_DIR)
    pca_coords, explained = project_pca_2d(x_model)
    plot_2d_clusters(
        coords=pca_coords,
        labels=labels,
        title=f"Clusters in PCA 2D (explained variance={explained:.2%})",
        output_path=FIGURES_DIR / "clusters_pca_2d.png",
    )

    umap_coords = project_umap_2d(x_model)
    if umap_coords is not None:
        plot_2d_clusters(
            coords=umap_coords,
            labels=labels,
            title="Clusters in UMAP 2D",
            output_path=FIGURES_DIR / "clusters_umap_2d.png",
        )
    else:
        print("UMAP not installed, skipping UMAP figure.")

    print(f"Pipeline completed with k={selected_k}. Outputs in: {OUTPUTS_DIR}")


if __name__ == "__main__":
    main()
