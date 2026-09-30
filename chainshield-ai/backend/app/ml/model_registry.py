"""Loads and validates the SIH Isolation Forest artifact saved by
scripts/train_sih_isolation_forest.py.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import joblib
import sklearn

logger = logging.getLogger("chainshield.ml")

BASE_DIR = Path(__file__).resolve().parents[1]  # this file sits at <repo_root>/app/ml/, so go up 2 levels

# Overridable via env var so a deployment can point at a model trained
# elsewhere without editing code.
SIH_MODEL_PATH = Path(
    os.environ.get("CHAINSHIELD_SIH_MODEL_PATH", BASE_DIR / "models" / "sih_isolation_forest.pkl")
)

REQUIRED_KEYS = {
    "model",
    "feature_names",
    "trained_at",
    "sklearn_version",
    "training_rows",
    "contamination",
    "dedupe_transactions",
}
REQUIRED_MODEL_METHODS = ("decision_function", "predict")


class InvalidModelArtifactError(ValueError):
    """Raised when a file at the model path exists but isn't a usable artifact."""


def _validate_artifact(artifact: Any, model_path: Path) -> None:
    """Check shape and basic sanity, not just key presence."""
    if not isinstance(artifact, dict):
        raise InvalidModelArtifactError(
            f"Invalid SIH model artifact at {model_path}: expected a dict, got {type(artifact).__name__}."
        )

    missing = REQUIRED_KEYS - artifact.keys()
    if missing:
        raise InvalidModelArtifactError(
            f"Invalid SIH model artifact at {model_path}: missing keys {sorted(missing)}."
        )

    model = artifact["model"]
    absent_methods = [m for m in REQUIRED_MODEL_METHODS if not hasattr(model, m)]
    if absent_methods:
        raise InvalidModelArtifactError(
            f"Invalid SIH model artifact at {model_path}: model object is missing "
            f"{absent_methods}. It may be corrupted or not the model this loader expects."
        )

    feature_names = artifact["feature_names"]
    if (
        not isinstance(feature_names, list)
        or not feature_names
        or not all(isinstance(f, str) for f in feature_names)
    ):
        raise InvalidModelArtifactError(
            f"Invalid SIH model artifact at {model_path}: 'feature_names' must be "
            "a non-empty list of strings."
        )
    if len(set(feature_names)) != len(feature_names):
        raise InvalidModelArtifactError(
            f"Invalid SIH model artifact at {model_path}: 'feature_names' has duplicates."
        )

    if not isinstance(artifact["training_rows"], int) or artifact["training_rows"] <= 0:
        raise InvalidModelArtifactError(
            f"Invalid SIH model artifact at {model_path}: 'training_rows' must be a positive int."
        )


def _warn_on_version_mismatch(artifact: dict, model_path: Path) -> None:
    trained_version = artifact.get("sklearn_version")
    if trained_version and trained_version != sklearn.__version__:
        logger.warning(
            "SIH model at %s was trained with scikit-learn %s, but %s is installed. "
            "Predictions may differ from training; retrain if results look off.",
            model_path,
            trained_version,
            sklearn.__version__,
        )


def load_sih_isolation_forest(model_path: Path = SIH_MODEL_PATH) -> dict:
    """
    Load and validate the SIH Isolation Forest artifact.

    Raises:
        FileNotFoundError: no file at model_path.
        InvalidModelArtifactError: file exists but isn't a usable artifact.

    Note: this loads a pickle via joblib. Only ever point it at a model file
    your own training script produced — pickle files can execute arbitrary
    code on load.
    """
    model_path = Path(model_path)

    if not model_path.is_file():
        raise FileNotFoundError(
            f"SIH Isolation Forest model not found: {model_path}. "
            "Run scripts/train_sih_isolation_forest.py first."
        )

    try:
        artifact = joblib.load(model_path)
    except Exception as exc:
        raise InvalidModelArtifactError(
            f"Could not load SIH model artifact at {model_path}: {exc}"
        ) from exc

    _validate_artifact(artifact, model_path)
    _warn_on_version_mismatch(artifact, model_path)

    logger.info(
        "Loaded SIH model from %s (trained_at=%s, training_rows=%d, features=%d)",
        model_path,
        artifact["trained_at"],
        artifact["training_rows"],
        len(artifact["feature_names"]),
    )
    return artifact