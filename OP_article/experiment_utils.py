"""Shared configuration and helpers for the OP article experiment pipeline."""

from __future__ import annotations

from functools import reduce
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "DATA"
SPLITS_DIR = DATA_DIR / "splits"
FIGURES_DIR = DATA_DIR / "figures"

RAW_DEV_PATH = DATA_DIR / "RAW_ARTICLE.csv"
EXTERNAL_PATH = DATA_DIR / "EVAL_2013_2014.csv"
DEV_NHANES_DIR = DATA_DIR
EXT_NHANES_DIR = DATA_DIR / "EVAL_2013_2014"
MIN_COHORT_AGE = 50
DEV_CLEAN_PATH = DATA_DIR / "DEV_CLEAN_COMPLETE.csv"
EXTERNAL_CLEAN_PATH = DATA_DIR / "EXTERNAL_CLEAN_COMPLETE.csv"
TRAIN_PATH = SPLITS_DIR / "train.csv"
TEST_PATH = SPLITS_DIR / "test.csv"
CTGAN_POOL_PATH = DATA_DIR / "SYNTHETIC_POOL.csv"
METADATA_PATH = PROJECT_ROOT / "metadata.json"

# ── Experiment constants ─────────────────────────────────────────────────────
RANDOM_STATE = 42
TEST_SIZE = 0.30
CV_FOLDS = 10

ID_COL = "SEQN"
LABEL_COL = "TARGET"
TSCORE_REF = 0.858
TSCORE_SCALE = 0.120
TSCORE_CUTOFF = -0.99

CAT_ALL = ["RIAGENDR", "DIQ010", "OSQ060", "OSQ150"]
VALID_CAT_CODES = [1, 2]

NUM_FEATURES = [
    "RIDAGEYR",
    "INDFMPIR",
    "BMXBMI",
    "LBXSCK",
    "LBDSCHSI",
    "LBXSAPSI",
    "LBXSUA",
    "LBDSTPSI",
    "LBDSGBSI",
    "LBXSOSSI",
    "LBXGH",
    "LBXMCVSI",
    "LBXRDW",
    "LBXNEPCT",
    "LBXMOPCT",
]
# OSQ060 is used for TARGET but excluded from predictors.
CAT_FEATURES = ["RIAGENDR", "OSQ150", "DIQ010"]
MODEL_FEATURES = NUM_FEATURES + CAT_FEATURES

NHANES_TO_PAPER = {
    "RIDAGEYR": "Age",
    "BMXBMI": "BMI",
    "INDFMPIR": "Income-to-poverty ratio",
    "LBXSCK": "Creatine phosphokinase (CPK)",
    "LBDSCHSI": "Total cholesterol",
    "LBXSAPSI": "Alkaline phosphatase (ALP)",
    "LBXSUA": "Uric acid",
    "LBDSTPSI": "Total protein",
    "LBDSGBSI": "Globulin",
    "LBXSOSSI": "Osmolality",
    "LBXGH": "Glycohemoglobin",
    "LBXMCVSI": "Mean cell volume",
    "LBXRDW": "Red cell distribution width",
    "LBXNEPCT": "Neutrophil percent",
    "LBXMOPCT": "Monocyte percent",
    "RIAGENDR": "Gender",
    "OSQ150": "Parental osteoporosis / fracture (OSQ150)",
    "DIQ010": "Diabetes",
}

# NHANES source tables -> columns kept when building cohort datasets.
# Development: NHANES 2017–2020 (P_* files). External: NHANES 2013–2014 ( *_H files).
DEV_NHANES_TABLES: dict[str, list[str]] = {
    "P_DXXFEM": [ID_COL, "DXXNKBMD"],
    "P_DEMO": [ID_COL, "RIDAGEYR", "RIAGENDR", "INDFMPIR"],
    "P_BMX": [ID_COL, "BMXBMI"],
    "P_BIOPRO": [
        ID_COL,
        "LBXSCK",
        "LBDSCHSI",
        "LBXSAPSI",
        "LBXSUA",
        "LBDSTPSI",
        "LBDSGBSI",
        "LBXSOSSI",
    ],
    "P_GHB": [ID_COL, "LBXGH"],
    "P_CBC": [ID_COL, "LBXMCVSI", "LBXRDW", "LBXNEPCT", "LBXMOPCT"],
    "P_DIQ": [ID_COL, "DIQ010"],
    "P_OSQ": [ID_COL, "OSQ060", "OSQ150"],
}
EXT_NHANES_TABLES: dict[str, list[str]] = {
    "DEMO_H": [ID_COL, "RIDAGEYR", "RIAGENDR", "INDFMPIR"],
    "BMX_H": [ID_COL, "BMXBMI"],
    "DXXFEM_H": [ID_COL, "DXXNKBMD"],
    "BIOPRO_H": [
        ID_COL,
        "LBXSCK",
        "LBDSCHSI",
        "LBXSAPSI",
        "LBXSUA",
        "LBDSTPSI",
        "LBDSGBSI",
        "LBXSOSSI",
    ],
    "GHB_H": [ID_COL, "LBXGH"],
    "DIQ_H": [ID_COL, "DIQ010"],
    "CBC_H": [ID_COL, "LBXMCVSI", "LBXRDW", "LBXNEPCT", "LBXMOPCT"],
    "OSQ_H": [ID_COL, "OSQ060", "OSQ150"],
}


def _resolve_nhanes_table_path(base_dir: Path, stem: str) -> Path:
    """Return the first existing `.xpt` or `.csv` file for a NHANES table stem."""
    for ext in (".xpt", ".csv"):
        candidate = base_dir / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"No NHANES table found for '{stem}' in {base_dir}")


def read_nhanes_table(path: Path, columns: list[str]) -> pd.DataFrame:
    """Read selected columns from a NHANES `.xpt` (SAS transport) or `.csv` file."""
    if path.suffix.lower() == ".xpt":
        df = pd.read_sas(path)
    else:
        df = pd.read_csv(path)
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise KeyError(f"{path.name} is missing columns: {missing}")
    return df[columns].copy()


def convert_xpt_directory_to_csv(
    source_dir: Path,
    *,
    dest_dir: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Path]:
    """Convert every `.xpt` in *source_dir* to CSV (same stem, optional separate dest)."""
    dest_dir = source_dir if dest_dir is None else dest_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    converted: dict[str, Path] = {}
    for xpt_path in sorted(source_dir.glob("*.xpt")):
        csv_path = dest_dir / f"{xpt_path.stem}.csv"
        if csv_path.exists() and not overwrite:
            converted[xpt_path.stem] = csv_path
            continue
        pd.read_sas(xpt_path).to_csv(csv_path, index=False)
        converted[xpt_path.stem] = csv_path
    return converted


def merge_nhanes_tables(
    table_map: dict[str, list[str]],
    base_dir: Path,
    *,
    how: Literal["inner", "outer"] = "outer",
    verbose: bool = False,
) -> pd.DataFrame:
    """Load NHANES tables and merge them on ``SEQN``."""
    frames: list[pd.DataFrame] = []
    for stem, columns in table_map.items():
        path = _resolve_nhanes_table_path(base_dir, stem)
        if verbose:
            print(f"Loading {path} …")
        frames.append(read_nhanes_table(path, columns))

    if not frames:
        raise ValueError("table_map is empty")

    merged = reduce(
        lambda left, right: pd.merge(left, right, on=ID_COL, how=how),
        frames,
    )
    return merged.reset_index(drop=True)


def gather_development_cohort(
    *,
    base_dir: Path = DEV_NHANES_DIR,
    min_age: int = MIN_COHORT_AGE,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Build the development (2017–2020) raw cohort.

    Outer-join NHANES tables on ``SEQN``, keep age ≥ ``min_age``, require femoral-neck BMD.
    """
    merged = merge_nhanes_tables(
        DEV_NHANES_TABLES,
        base_dir,
        how="outer",
        verbose=verbose,
    )
    aged = merged.loc[merged["RIDAGEYR"] >= min_age].copy()
    return aged.dropna(subset=["DXXNKBMD"]).reset_index(drop=True)


def finalize_external_cohort(
    df: pd.DataFrame,
    *,
    min_age: int = MIN_COHORT_AGE,
) -> pd.DataFrame:
    """
    Turn the merged external tables into ``EVAL_2013_2014.csv``.

    Differs from ``prepare_external`` (notebook 2): survey-code cleaning is limited
    to OSQ/DIQ, the T-score is not rounded before TARGET, and ``dropna()`` removes
    any row with a missing value in any column, not just the model features.
    """
    out = df.copy()
    for col in ("OSQ060", "OSQ150", "DIQ010"):
        if col in out.columns:
            out.loc[~out[col].isin(VALID_CAT_CODES), col] = np.nan
    out["TSCORE"] = (out["DXXNKBMD"] - TSCORE_REF) / TSCORE_SCALE
    out[LABEL_COL] = (
        (out["TSCORE"] <= TSCORE_CUTOFF) | (out["OSQ060"] == 1)
    ).astype(int)
    out = out.loc[out["RIDAGEYR"] >= min_age].copy()
    return out.dropna().reset_index(drop=True)


def gather_external_cohort(
    *,
    base_dir: Path = EXT_NHANES_DIR,
    min_age: int = MIN_COHORT_AGE,
    finalize: bool = False,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Build the external (2013–2014) cohort from NHANES ``*_H`` files.

    With ``finalize=False`` (default), returns the inner-joined feature table only.
    With ``finalize=True``, also applies invalid survey codes, T-score / TARGET,
    the age filter, and complete-case selection.
    """
    merged = merge_nhanes_tables(
        EXT_NHANES_TABLES,
        base_dir,
        how="inner",
        verbose=verbose,
    )
    if not finalize:
        return merged

    return finalize_external_cohort(merged, min_age=min_age)


def build_gathered_datasets(
    *,
    save: bool = True,
    overwrite: bool = False,
    verbose: bool = False,
) -> dict[str, pd.DataFrame]:
    """
    Reproduce ``RAW_ARTICLE.csv`` and ``EVAL_2013_2014.csv`` from NHANES sources.

    Returns ``{"development": df_dev, "external": df_ext}``.
    """
    df_dev = gather_development_cohort(verbose=verbose)
    df_ext = gather_external_cohort(finalize=True, verbose=verbose)

    if save:
        if overwrite or not RAW_DEV_PATH.exists():
            df_dev.to_csv(RAW_DEV_PATH, index=False)
        if overwrite or not EXTERNAL_PATH.exists():
            df_ext.to_csv(EXTERNAL_PATH, index=False)

    return {"development": df_dev, "external": df_ext}


def ensure_dirs() -> None:
    for path in (SPLITS_DIR, FIGURES_DIR):
        path.mkdir(parents=True, exist_ok=True)


def apply_tscore_and_target(df: pd.DataFrame) -> pd.DataFrame:
    """Compute T-score and binary TARGET using the article rule."""
    out = df.copy()
    out["TSCORE"] = (out["DXXNKBMD"] - TSCORE_REF) / TSCORE_SCALE
    out["TSCORE_ROUNDED"] = out["TSCORE"].round(3)
    out[LABEL_COL] = (
        (out["TSCORE_ROUNDED"] <= TSCORE_CUTOFF) | (out["OSQ060"] == 1)
    ).astype(int)
    return out


def clean_categorical_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Set invalid NHANES survey codes to NA, then keep rows with valid 1/2 codes."""
    out = df.copy()
    for col in CAT_ALL:
        if col in out.columns:
            out.loc[~out[col].isin(VALID_CAT_CODES), col] = np.nan
    valid_mask = out[CAT_ALL].notna().all(axis=1)
    return out.loc[valid_mask].copy().reset_index(drop=True)


def to_complete_cases(df: pd.DataFrame) -> pd.DataFrame:
    """Keep rows with no missing model features."""
    return df.dropna(subset=MODEL_FEATURES).copy().reset_index(drop=True)


def prepare_development_raw(df: pd.DataFrame) -> pd.DataFrame:
    out = clean_categorical_codes(df)
    out = apply_tscore_and_target(out)
    return to_complete_cases(out)


def prepare_external(df: pd.DataFrame) -> pd.DataFrame:
    out = clean_categorical_codes(df)
    if "TSCORE" not in out.columns or LABEL_COL not in out.columns:
        out = apply_tscore_and_target(out)
    return to_complete_cases(out)


def add_labels_to_synthetic(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute TARGET on generated rows from DXXNKBMD and OSQ060."""
    out = df.copy()
    for col in CAT_ALL:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
            out.loc[~out[col].isin(VALID_CAT_CODES), col] = np.nan
            out[col] = out[col].round().astype("Int64")
    out = apply_tscore_and_target(out)
    return out


def build_preprocessor():
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import StandardScaler

    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUM_FEATURES),
            ("cat", "passthrough", CAT_FEATURES),
        ],
        remainder="drop",
    )


def get_model_search_spaces() -> dict[str, tuple]:
    """Model name -> (estimator, param_grid) for GridSearchCV."""
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold
    from sklearn.naive_bayes import GaussianNB
    from sklearn.neural_network import MLPClassifier
    from sklearn.svm import SVC

    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    spaces = {
        "LR": (
            LogisticRegression(max_iter=3000, solver="liblinear", random_state=RANDOM_STATE),
            {"clf__C": [0.01, 0.1, 1.0, 10.0]},
        ),
        "RF": (
            RandomForestClassifier(random_state=RANDOM_STATE),
            {"clf__n_estimators": [100, 200], "clf__max_depth": [None, 8]},
        ),
        "GBM": (
            GradientBoostingClassifier(random_state=RANDOM_STATE),
            {"clf__n_estimators": [100], "clf__learning_rate": [0.05, 0.1]},
        ),
        "SVM": (
            SVC(probability=True, random_state=RANDOM_STATE),
            {"clf__C": [0.1, 1.0], "clf__gamma": ["scale"]},
        ),
        "NB": (GaussianNB(), {}),
        "ANN": (
            MLPClassifier(max_iter=1000, random_state=RANDOM_STATE),
            {"clf__hidden_layer_sizes": [(64,), (64, 32)], "clf__alpha": [0.001, 0.01]},
        ),
    }
    return spaces, cv


def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    model_name: str = "LR",
    *,
    fast: bool = False,
):
    """Fit preprocessor + classifier with optional grid search."""
    from sklearn.model_selection import GridSearchCV
    from sklearn.pipeline import Pipeline

    spaces, cv = get_model_search_spaces()
    estimator, param_grid = spaces[model_name]
    pipe = Pipeline([("prep", build_preprocessor()), ("clf", estimator)])

    if fast or not param_grid:
        pipe.fit(X_train, y_train)
        return pipe

    search = GridSearchCV(
        pipe,
        param_grid=param_grid,
        cv=cv,
        scoring="roc_auc",
        n_jobs=-1,
        refit=True,
    )
    search.fit(X_train, y_train)
    return search.best_estimator_


def evaluate_model(
    model,
    X: pd.DataFrame,
    y: pd.Series,
) -> dict:
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

    proba = model.predict_proba(X[MODEL_FEATURES])[:, 1]
    pred = model.predict(X[MODEL_FEATURES])
    return {
        "auc": roc_auc_score(y, proba),
        "y_proba": proba,
        "y_pred": pred,
        "report": classification_report(y, pred, output_dict=True),
        "confusion_matrix": confusion_matrix(y, pred),
    }


def stratified_subsample(
    df: pd.DataFrame,
    n: int,
    *,
    random_state: int,
) -> pd.DataFrame:
    """Return n stratified rows; n=0 yields an empty frame (same columns)."""
    n = int(n)
    if n <= 0 or len(df) == 0:
        return df.iloc[0:0].copy()
    if n >= len(df):
        return df.copy().reset_index(drop=True)

    from sklearn.model_selection import train_test_split

    # test_size=n returns exactly n rows in the second split (no train_size=0 edge case)
    _, sample = train_test_split(
        df,
        test_size=n,
        stratify=df[LABEL_COL],
        random_state=random_state,
    )
    return sample.reset_index(drop=True)


def plot_roc_curves(results: dict, title: str, save_path: Path | None = None) -> None:
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve

    plt.figure(figsize=(7, 6))
    for label, payload in results.items():
        fpr, tpr, _ = roc_curve(payload["y_true"], payload["y_proba"])
        plt.plot(fpr, tpr, label=f"{label} (AUC={payload['auc']:.3f})")
    plt.plot([0, 1], [0, 1], "k--", alpha=0.4)
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title(title)
    plt.legend(loc="lower right")
    plt.tight_layout()
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_confusion(cm: np.ndarray, title: str, save_path: Path | None = None) -> None:
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title(title)
    plt.tight_layout()
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def set_reproducibility(seed: int = RANDOM_STATE) -> None:
    """Fix Python, NumPy, and PyTorch RNGs for reproducible CTGAN training/sampling."""
    import random

    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
