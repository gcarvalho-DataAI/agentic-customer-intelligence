from __future__ import annotations

from datetime import datetime

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

FREQUENCY_ORDER = {
    "baixa": 1,
    "media": 2,
    "média": 2,
    "alta": 3,
    "muito_alta": 4,
    "recorrente": 5,
}

LOW_CARDINALITY_BASE = [
    "canal_preferido",
    "categoria_favorita",
    "regiao",
    "pagamento",
    "genero",
]

HIGH_CARDINALITY = [
    "marca_preferida",
    "influenciador",
]

NUMERIC_MODEL_FEATURES_BASE = [
    "idade",
    "ticket_medio",
    "qtd_itens",
    "marca_preferida_freq",
    "influenciador_freq",
]


def _compute_age_from_birthdate(series: pd.Series, reference_date: datetime | None = None) -> pd.Series:
    ref = reference_date or datetime.utcnow()
    dates = pd.to_datetime(series, errors="coerce", dayfirst=True)
    had_birthday = (dates.dt.month < ref.month) | (
        (dates.dt.month == ref.month) & (dates.dt.day <= ref.day)
    )
    age = ref.year - dates.dt.year - (~had_birthday).astype("Int64")
    return age.where(dates.notna())


def _build_age_band(age: pd.Series) -> pd.Series:
    bins = [0, 24, 34, 44, 54, 200]
    labels = ["18-24", "25-34", "35-44", "45-54", "55+"]
    return pd.cut(age, bins=bins, labels=labels)


def _add_frequency_features(df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    out = df.copy()
    normalized = out["frequencia_compra"].astype(str).str.strip().str.lower()
    mapped = normalized.map(FREQUENCY_ORDER)
    has_unknown = mapped.isna().any()
    if not has_unknown:
        out["frequencia_compra_ord"] = mapped.astype(int)
    return out, not has_unknown


def _add_frequency_encoded_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    n_rows = len(out)
    for column in HIGH_CARDINALITY:
        freq_col = f"{column}_freq"
        out[freq_col] = out[column].value_counts(dropna=False).div(n_rows).reindex(out[column]).to_numpy()
    return out


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[str], list[str]]:
    out = df.copy()
    out["idade"] = _compute_age_from_birthdate(out["data_nascimento"])
    out["faixa_etaria"] = _build_age_band(out["idade"])
    out = _add_frequency_encoded_columns(out)
    out, has_frequency_ordinal = _add_frequency_features(out)

    categorical_features = list(LOW_CARDINALITY_BASE)
    numeric_features = list(NUMERIC_MODEL_FEATURES_BASE)
    if has_frequency_ordinal:
        numeric_features.append("frequencia_compra_ord")
    else:
        categorical_features.append("frequencia_compra")

    df_reference = out.copy()
    model_cols = numeric_features + categorical_features
    df_model = out[model_cols].copy()

    # Guardrail to keep pipeline fitting resilient if date parsing produced NaNs.
    df_model["idade"] = df_model["idade"].fillna(df_model["idade"].median())

    return df_model, df_reference, numeric_features, categorical_features


def build_preprocessing_pipeline(
    numeric_features: list[str],
    categorical_features: list[str],
) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("numeric", Pipeline([("scaler", StandardScaler())]), numeric_features),
            (
                "categorical",
                Pipeline([("one_hot", OneHotEncoder(handle_unknown="ignore"))]),
                categorical_features,
            ),
        ]
    )
