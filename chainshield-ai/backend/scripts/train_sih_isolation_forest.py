"""
Trains an Isolation Forest on SIH transaction features and saves it, together
with the metadata needed to use it safely later (feature order, contamination,
row count, training time).

Usage:
    python -m scripts.train_sih_isolation_forest
    python -m scripts.train_sih_isolation_forest --contamination 0.05 --sample 2000
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest

from app.data_sources.sih_source import SIHDataSource
from app.entity_graph.entity_graph import EntityGraphEngine
from app.feature_engine.feature_extractor import FeatureExtractionEngine

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "app" / "models" / "sih_isolation_forest.pkl"


from app.ml.model_registry import load_sih_isolation_forest  # re-exported for convenience

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s  %(message)s")
logger = logging.getLogger("train_sih_isolation_forest")


class TrainingDataError(RuntimeError):
    """Raised when the feature matrix is not fit to train on."""


@dataclass(frozen=True)
class TrainingConfig:
    model_path: Path = DEFAULT_MODEL_PATH
    n_estimators: int = 100
    contamination: float = 0.10
    random_state: int = 42
    sample: int | None = None  # cap on row count, for quick local runs
    dedupe_transactions: bool = True  # see _select_training_rows() docstring
    n_jobs: int = -1


@dataclass
class TrainingReport:
    rows_loaded: int
    rows_trained_on: int
    feature_count: int
    feature_names: list[str]
    anomaly_fraction: float
    score_min: float
    score_max: float
    top_anomalies: pd.DataFrame = field(repr=False)

    def log_summary(self) -> None:
        logger.info("Rows loaded        : %d", self.rows_loaded)
        logger.info("Rows trained on    : %d", self.rows_trained_on)
        logger.info("Feature count      : %d", self.feature_count)
        logger.info(
            "Anomaly score range: [%.4f, %.4f] (lower = more anomalous)",
            self.score_min,
            self.score_max,
        )
        logger.info(
            "Flagged as anomaly : %d rows (%.1f%%)",
            round(self.anomaly_fraction * self.rows_trained_on),
            self.anomaly_fraction * 100,
        )
        logger.info(
            "Top 5 anomalies:\n%s",
            self.top_anomalies.head(5).to_string(index=False),
        )


def _select_training_rows(
    features: pd.DataFrame,
    config: TrainingConfig,
) -> pd.DataFrame:
    """
    Reduce the row-level feature table to what the model should actually see.

    `FeatureExtractionEngine.extract()` returns one row per network
    *observation* (an IP/port seeing a transaction), not one row per
    transaction. A transaction observed from 10 IPs contributes 10 identical
    copies of its own amount/graph features. Training on that directly lets
    high-traffic transactions dominate the fitted trees and skews which score
    counts as the 10th-percentile "anomaly" cutoff.

    With `dedupe_transactions=True` (the default) we keep one row per
    transaction_id, so every transaction has equal weight in training. The
    per-observation detail (which IP, which port) still lives in the graph
    and correlation engines for investigation; it is not needed for training.
    """
    if not config.dedupe_transactions:
        return features

    before = len(features)
    deduped = features.drop_duplicates(subset="transaction_id", keep="first")
    if len(deduped) < before:
        logger.info(
            "Deduplicated %d observation rows down to %d transactions before training.",
            before,
            len(deduped),
        )
    return deduped


def _validate_feature_matrix(X: pd.DataFrame) -> None:
    """Fail loudly and specifically, instead of letting sklearn fail cryptically."""
    if X.empty:
        raise TrainingDataError("Feature matrix has zero rows.")

    bad = X.columns[~np.isfinite(X.to_numpy()).all(axis=0)]
    if len(bad):
        raise TrainingDataError(
            f"Feature matrix has NaN/inf values in columns: {list(bad)}. "
            "Fix upstream in FeatureExtractionEngine rather than dropping rows here."
        )

    constant = X.columns[X.nunique(dropna=False) <= 1]
    if len(constant):
        logger.warning(
            "These features are constant across all rows and add no signal: %s",
            list(constant),
        )


def build_feature_matrix(config: TrainingConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (model_matrix, aligned identifier columns) for the rows actually trained on."""
    logger.info("Loading SIH dataset...")
    data = SIHDataSource().get_all_transactions()
    if config.sample:
        data = data.sample(n=min(config.sample, len(data)), random_state=config.random_state)
    logger.info("Transactions loaded: %d", len(data))

    logger.info("Building entity graph...")
    graph = EntityGraphEngine(data)

    logger.info("Extracting SIH features...")
    feature_engine = FeatureExtractionEngine(data, graph_engine=graph)
    features = feature_engine.extract()

    training_rows = _select_training_rows(features, config)
    identifiers = training_rows[["transaction_id", "wallet_address", "ip_address"]]
    X = training_rows[feature_engine.feature_names].astype(float)

    _validate_feature_matrix(X)
    return X, identifiers


def train_sih_isolation_forest(config: TrainingConfig | None = None) -> tuple[IsolationForest, TrainingReport]:
    config = config or TrainingConfig()

    X, identifiers = build_feature_matrix(config)
    logger.info("Feature matrix shape: %s", X.shape)

    logger.info(
        "Training Isolation Forest (n_estimators=%d, contamination=%s)...",
        config.n_estimators,
        config.contamination,
    )
    model = IsolationForest(
        n_estimators=config.n_estimators,
        contamination=config.contamination,
        random_state=config.random_state,
        n_jobs=config.n_jobs,
    )
    model.fit(X)

    scores = model.decision_function(X)  # higher = more normal
    predictions = model.predict(X)  # -1 = anomaly, 1 = normal

    top_anomalies = (
        identifiers.assign(anomaly_score=scores)
        .sort_values("anomaly_score")
        .reset_index(drop=True)
    )

    report = TrainingReport(
        rows_loaded=len(X),
        rows_trained_on=len(X),
        feature_count=X.shape[1],
        feature_names=list(X.columns),
        anomaly_fraction=float((predictions == -1).mean()),
        score_min=float(scores.min()),
        score_max=float(scores.max()),
        top_anomalies=top_anomalies,
    )

    _save_model(model, config, report)
    return model, report


def _save_model(model: IsolationForest, config: TrainingConfig, report: TrainingReport) -> None:
    """
    Save the model together with the metadata needed to reuse it safely:
    the exact feature order it was trained on, so a later mismatch (a
    reordered or renamed feature) fails fast at load time instead of silently
    scoring on the wrong columns.
    """
    config.model_path.parent.mkdir(parents=True, exist_ok=True)

    artifact = {
        "model": model,
        "feature_names": report.feature_names,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "sklearn_version": sklearn.__version__,
        "training_rows": report.rows_trained_on,
        "contamination": config.contamination,
        "dedupe_transactions": config.dedupe_transactions,
    }
    joblib.dump(artifact, config.model_path)
    logger.info("Model saved: %s", config.model_path)


def score_with_saved_model(X: pd.DataFrame, model_path: Path = DEFAULT_MODEL_PATH) -> np.ndarray:
    """
    Score new data with the saved model, guarding against a feature mismatch
    that would otherwise silently score on the wrong columns.
    """
    artifact = load_sih_isolation_forest(model_path)
    expected = artifact["feature_names"]
    missing = set(expected) - set(X.columns)
    if missing:
        raise ValueError(f"Input is missing features the model was trained on: {sorted(missing)}")
    return artifact["model"].decision_function(X[expected])


def _parse_args(argv: list[str] | None = None) -> TrainingConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.10,
        help="Expected fraction of anomalies. Only meaningful if you have a "
        "reason to believe fraud is ~this common in the data; otherwise "
        "leave at 0.10 or pass 'auto'-equivalent by tuning after review.",
    )
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--sample", type=int, default=None, help="Cap rows, for a quick local run")
    parser.add_argument(
        "--no-dedupe",
        dest="dedupe_transactions",
        action="store_false",
        help="Train on one row per network observation instead of one per transaction",
    )
    args = parser.parse_args(argv)
    return TrainingConfig(
        model_path=args.model_path,
        n_estimators=args.n_estimators,
        contamination=args.contamination,
        random_state=args.random_state,
        sample=args.sample,
        dedupe_transactions=args.dedupe_transactions,
    )


def main(argv: list[str] | None = None) -> int:
    config = _parse_args(argv)
    try:
        _, report = train_sih_isolation_forest(config)
    except TrainingDataError as exc:
        logger.error("Training data problem: %s", exc)
        return 1
    except FileNotFoundError as exc:
        logger.error("Data source problem: %s", exc)
        return 1

    report.log_summary()
    return 0


if __name__ == "__main__":
    sys.exit(main())