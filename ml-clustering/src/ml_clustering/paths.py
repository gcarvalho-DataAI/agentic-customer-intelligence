from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = PROJECT_ROOT / "data" / "dados_sinteticos.csv"
ML_ROOT = PROJECT_ROOT / "ml-clustering"
OUTPUTS_DIR = ML_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"

