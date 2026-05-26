from __future__ import annotations

from pathlib import Path

import pandas as pd


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


def load_customer_data(path: str | Path) -> pd.DataFrame:
    """Load the synthetic customer dataset."""
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    return pd.read_csv(dataset_path)


def validate_schema(df: pd.DataFrame) -> dict[str, object]:
    """Validate required columns and return data quality diagnostics."""
    if df.empty:
        raise ValueError("Dataset is empty.")

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    diagnostics = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "null_values": df[REQUIRED_COLUMNS].isna().sum().to_dict(),
        "duplicated_rows": int(df.duplicated().sum()),
        "dtypes": {column: str(dtype) for column, dtype in df[REQUIRED_COLUMNS].dtypes.items()},
    }

    return diagnostics

