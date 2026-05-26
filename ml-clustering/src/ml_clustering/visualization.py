from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def plot_kmeans_metrics(metrics_df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(metrics_df["k"], metrics_df["inertia"], marker="o")
    ax.set_title("Elbow Method")
    ax.set_xlabel("k")
    ax.set_ylabel("Inertia")
    fig.tight_layout()
    fig.savefig(output_dir / "elbow_method.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(metrics_df["k"], metrics_df["silhouette_score"], marker="o")
    ax.set_title("Silhouette Scores")
    ax.set_xlabel("k")
    ax.set_ylabel("Silhouette Score")
    fig.tight_layout()
    fig.savefig(output_dir / "silhouette_scores.png", dpi=160)
    plt.close(fig)


def plot_2d_clusters(coords, labels, title: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(coords[:, 0], coords[:, 1], c=labels, s=18, cmap="tab10", alpha=0.8)
    ax.set_title(title)
    ax.set_xlabel("Component 1")
    ax.set_ylabel("Component 2")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)

