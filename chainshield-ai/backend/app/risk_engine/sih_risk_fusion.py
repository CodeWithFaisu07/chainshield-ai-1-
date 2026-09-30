from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd

from app.ml.model_registry import load_sih_isolation_forest


DEFAULT_MODEL_PATH: Final[Path] = (
    Path(__file__).resolve().parents[1] / "models" / "sih_isolation_forest.pkl"
)

MODEL_NAME: Final[str] = "SIH Isolation Forest"

DISCLAIMER: Final[str] = (
    "Anomaly score is an investigative signal based on the SIH Isolation "
    "Forest model; it is not proof of malicious or illegal activity."
)

# Isolation Forest `decision_function` returns values roughly in [-0.5, 0.5],
# where lower means more anomalous. Shifting by 0.5 and flipping the sign
# maps that range onto [0, 1], which is then scaled to a 0-100 score.
_SCORE_OFFSET: Final[float] = 0.5
_SCORE_SCALE: Final[float] = 100.0

# Features surfaced to analysts as transparent evidence.
# Each entry is:
# (evidence type, feature name, cast function)
#
# No arbitrary "danger" thresholds are applied to these values.
EVIDENCE_FEATURES: Final[tuple[tuple[str, str, type], ...]] = (
    ("transaction", "feature_btc_amount", float),
    ("network", "feature_ip_tx_count", int),
    ("network", "feature_port_tx_count", int),
    ("network", "feature_wallet_tx_count", int),
    ("temporal", "feature_is_night", int),
    ("graph", "feature_graph_related_transactions", int),
    ("graph", "feature_graph_cluster_transactions", int),
)


class SIHRiskFusion:
    """
    Risk fusion engine for the SIH transaction-analysis pipeline.

    This module is intentionally separate from the legacy Elliptic
    RiskEngine in fusion.py.

    Important:
        An anomaly is an investigative signal, not proof of malicious
        or illegal activity.
    """

    def __init__(self, model_path: Path | str = DEFAULT_MODEL_PATH) -> None:
        self.model_path = Path(model_path)

        artifact = load_sih_isolation_forest(self.model_path)

        self.model = artifact["model"]
        self.feature_names: list[str] = list(artifact["feature_names"])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_transaction(
        self, feature_row: pd.Series | Mapping[str, Any]
    ) -> dict[str, Any]:
        """
        Score one SIH transaction using the trained Isolation Forest.

        The input must contain every feature expected by the saved model,
        and every value must be a finite number.
        """

        row = self._normalize_row(feature_row)

        X = self._build_feature_matrix([row])

        return self._score_matrix(X, [row])[0]

    def score_batch(self, frame: pd.DataFrame) -> list[dict[str, Any]]:
        """
        Score many transactions in a single vectorized model call.

        Returns one result per row, in the same order as `frame`.
        """

        if not isinstance(frame, pd.DataFrame):
            raise TypeError("frame must be a pandas DataFrame")

        if frame.empty:
            return []

        rows = frame.to_dict(orient="records")

        X = self._build_feature_matrix(rows)

        return self._score_matrix(X, rows)

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_row(
        feature_row: pd.Series | Mapping[str, Any],
    ) -> dict[str, Any]:
        """Normalize a Series or mapping into a plain dictionary."""

        if isinstance(feature_row, pd.Series):
            return feature_row.to_dict()

        if isinstance(feature_row, Mapping):
            return dict(feature_row)

        raise TypeError(
            "feature_row must be a pandas Series or a mapping"
        )

    def _build_feature_matrix(
        self,
        rows: list[dict[str, Any]],
    ) -> np.ndarray:
        """
        Convert rows into a float matrix ordered like the model's features.

        Raises a ValueError that names every offending feature, so callers
        can fix all problems in one pass instead of one at a time.
        """

        matrix = np.empty(
            (len(rows), len(self.feature_names)),
            dtype=float,
        )

        for i, row in enumerate(rows):

            missing = [
                name
                for name in self.feature_names
                if name not in row
            ]

            if missing:
                raise ValueError(
                    f"Row {i}: missing SIH model features: {missing}"
                )

            invalid = []

            for j, name in enumerate(self.feature_names):
                value = self._to_finite_float(row[name])

                if value is None:
                    invalid.append(name)
                else:
                    matrix[i, j] = value

            if invalid:
                raise ValueError(
                    f"Row {i}: features with missing or non-finite "
                    f"values: {invalid}"
                )

        return matrix

    @staticmethod
    def _to_finite_float(value: Any) -> float | None:
        """Return `value` as a finite float, or None if impossible."""

        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        return number if np.isfinite(number) else None

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _score_matrix(
        self,
        X: np.ndarray,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Run the Isolation Forest model and build investigation results.

        The DataFrame preserves the feature names used during model
        training, preventing sklearn feature-name warnings.
        """

        X_named = pd.DataFrame(
            X,
            columns=self.feature_names,
        )

        raw_scores = self.model.decision_function(X_named)

        predictions = self.model.predict(X_named)

        results = []

        for raw_score, prediction, row in zip(
            raw_scores,
            predictions,
            rows,
        ):
            anomaly_score = self._to_anomaly_score(
                float(raw_score)
            )

            results.append(
                {
                    "risk_score": anomaly_score,
                    "anomaly_score": anomaly_score,
                    "raw_anomaly_score": round(
                        float(raw_score),
                        6,
                    ),
                    "is_anomaly": int(prediction) == -1,
                    "model": MODEL_NAME,
                    "feature_count": len(self.feature_names),
                    "evidence": self._build_evidence(row),
                    "disclaimer": DISCLAIMER,
                }
            )

        return results

    @staticmethod
    def _to_anomaly_score(
        raw_score: float,
    ) -> float:
        """
        Map an Isolation Forest decision value to a bounded 0-100 score.
        """

        bounded = float(
            np.clip(
                _SCORE_OFFSET - raw_score,
                0.0,
                1.0,
            )
        )

        return round(
            bounded * _SCORE_SCALE,
            2,
        )

    @staticmethod
    def _build_evidence(
        row: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Return transparent feature evidence.

        Features absent from the row are skipped rather than raising,
        because evidence is informational and must never block scoring.
        """

        return [
            {
                "type": kind,
                "feature": feature,
                "value": cast(row[feature]),
            }
            for kind, feature, cast in EVIDENCE_FEATURES
            if feature in row
        ]