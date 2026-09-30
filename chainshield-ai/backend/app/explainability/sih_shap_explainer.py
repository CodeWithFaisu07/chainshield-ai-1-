from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
import shap


class SIHSHAPExplainer:
    """
    Generates SHAP-based feature contributions
    for the SIH Isolation Forest model.

    SHAP values explain how each feature pushed the model's output for a
    transaction. They are an investigative aid, not proof of wrongdoing.
    """

    def __init__(self, model: Any) -> None:
        self.model = model
        self.explainer = shap.TreeExplainer(model)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def explain(
        self,
        feature_frame: pd.DataFrame,
        feature_names: Sequence[str],
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Explain the first row of `feature_frame`.

        Returns contributions sorted by absolute impact (largest first).
        Use `top_k` to keep only the strongest contributors.
        Returns an empty list if the frame is empty.
        """

        if feature_frame.empty:
            return []

        return self.explain_batch(
            feature_frame.iloc[[0]], feature_names, top_k=top_k
        )[0]

    def explain_batch(
        self,
        feature_frame: pd.DataFrame,
        feature_names: Sequence[str],
        top_k: int | None = None,
    ) -> list[list[dict[str, Any]]]:
        """
        Explain every row of `feature_frame` with a single SHAP call.

        Returns one sorted contribution list per row, in row order.
        """

        if top_k is not None and top_k < 1:
            raise ValueError("top_k must be a positive integer or None")

        if feature_frame.empty:
            return []

        names = list(feature_names)
        X = self._prepare_matrix(feature_frame, names)
        shap_values = self._compute_shap_values(X, expected_columns=len(names))

        return [
            self._rank_contributions(names, row_values, top_k)
            for row_values in shap_values
        ]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _prepare_matrix(
        feature_frame: pd.DataFrame, names: list[str]
    ) -> pd.DataFrame:
        """Select model features in order and make sure they are finite floats."""

        missing = [name for name in names if name not in feature_frame.columns]
        if missing:
            raise ValueError(f"Missing SHAP input features: {missing}")

        try:
            X = feature_frame[names].astype(float)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "SHAP input features must be numeric"
            ) from exc

        invalid = [
            name for name in names if not np.isfinite(X[name].to_numpy()).all()
        ]
        if invalid:
            raise ValueError(
                f"Features with missing or non-finite values: {invalid}"
            )

        return X

    def _compute_shap_values(
        self, X: pd.DataFrame, expected_columns: int
    ) -> np.ndarray:
        """
        Return a 2D array of shape (n_rows, n_features).

        Some SHAP versions return a list of arrays (one per output); for the
        Isolation Forest there is a single output, so the first is used.
        """

        raw = self.explainer.shap_values(X)

        if isinstance(raw, list):
            raw = raw[0]

        values = np.asarray(raw, dtype=float)

        if values.ndim == 1:
            values = values.reshape(1, -1)

        if values.shape != (len(X), expected_columns):
            raise ValueError(
                f"Unexpected SHAP output shape {values.shape}; expected "
                f"({len(X)}, {expected_columns})"
            )

        return values

    @staticmethod
    def _rank_contributions(
        names: list[str],
        values: np.ndarray,
        top_k: int | None,
    ) -> list[dict[str, Any]]:
        contributions = [
            {
                "feature": name,
                "shap_value": float(value),
                "importance": abs(float(value)),
            }
            for name, value in zip(names, values)
        ]

        contributions.sort(key=lambda item: item["importance"], reverse=True)

        return contributions if top_k is None else contributions[:top_k]