from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:  # type hints only, keeps the two engines loosely coupled
    from app.entity_graph.entity_graph import EntityGraphEngine

MAX_PORT = 65_535
NIGHT_HOURS = frozenset({0, 1, 2, 3, 4, 5})

# Feature names are defined once, so stats / model matrices can never drift
# out of sync with what extract() actually produces.
TRANSACTION_FEATURES = (
    "feature_btc_amount",
    "feature_amount_vs_wallet_mean",
)
NETWORK_FEATURES = (
    "feature_ip_tx_count",
    "feature_port_tx_count",
    "feature_wallet_tx_count",
    "feature_ip_unique_wallets",
    "feature_wallet_unique_ips",
    "feature_ip_unique_ports",
)
TEMPORAL_FEATURES = (
    "feature_hour",
    "feature_day_of_week",
    "feature_is_night",
    "feature_is_weekend",
    "feature_ip_daily_tx_count",
    "feature_wallet_is_first_tx",
    "feature_wallet_seconds_since_prev_tx",
)
FEATURE_COLUMNS = TRANSACTION_FEATURES + NETWORK_FEATURES + TEMPORAL_FEATURES

MISSING_SENTINEL = -1  # used only for unparseable timestamps (hour / weekday)


@dataclass(frozen=True)
class FeatureConfig:
    """Column mapping for the feature extraction engine."""

    transaction_column: str = "transaction_id"
    wallet_column: str = "wallet_address"
    ip_column: str = "ip_address"
    port_column: str = "port_no"
    timestamp_column: str = "timestamp"
    amount_column: str = "bitcoin_transferred"

    @property
    def required_columns(self) -> tuple[str, ...]:
        return (
            self.transaction_column,
            self.wallet_column,
            self.ip_column,
            self.port_column,
            self.timestamp_column,
            self.amount_column,
        )


class FeatureExtractionEngine:
    """
    Extracts transaction, network and temporal features from the validated
    SIH dataset. Output has one row per input observation, with identifier
    columns first and numeric `feature_*` columns after.

    Notes:
        * Counts use *unique transaction ids*, so a transaction that appears
          on several rows is not counted several times.
        * Output has no NaN in feature columns: missing values become 0
          (counts / amounts) or -1 (hour / weekday of an unparseable timestamp).
        * Features are computed over the WHOLE dataset. When training a model,
          split by wallet / IP group or by time, otherwise information from the
          test rows leaks into the training features.
        * Pass `graph_engine` to append the graph features (feature_graph_*).
          Rows are matched on transaction_id; a transaction unknown to the graph
          gets 0 for every graph feature and is counted in the stats.
    """

    ID_COLUMNS = ("transaction_id", "wallet_address", "ip_address", "port_no", "timestamp")

    def __init__(
        self,
        data: pd.DataFrame,
        graph_engine: EntityGraphEngine | None = None,
        config: FeatureConfig | None = None,
    ) -> None:
        if graph_engine is not None and not hasattr(graph_engine, "get_graph_feature_table"):
            raise TypeError("graph_engine must provide get_graph_feature_table()")

        self.config = config or FeatureConfig()
        self.graph_engine = graph_engine
        self.data = self._validate_and_prepare(data)
        self._features: pd.DataFrame | None = None
        self._graph_unmatched_rows = 0

    # ------------------------------------------------------------------ #
    # Validation and cleaning
    # ------------------------------------------------------------------ #
    def _validate_and_prepare(self, data: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(data, pd.DataFrame):
            raise TypeError("data must be a pandas DataFrame")

        cfg = self.config
        missing = sorted(set(cfg.required_columns) - set(data.columns))
        if missing:
            raise ValueError(f"Feature dataset is missing required columns: {missing}")
        if data.empty:
            raise ValueError("Feature dataset cannot be empty")

        result = data.copy().reset_index(drop=True)

        for column in (cfg.transaction_column, cfg.wallet_column, cfg.ip_column):
            cleaned = result[column].astype("string").str.strip()
            result[column] = cleaned.mask((cleaned == "").fillna(False))

        port = pd.to_numeric(result[cfg.port_column], errors="coerce")
        valid_port = port.notna() & (port % 1 == 0) & port.between(0, MAX_PORT)
        result[cfg.port_column] = port.where(valid_port).astype("Int64")

        result[cfg.amount_column] = pd.to_numeric(result[cfg.amount_column], errors="coerce")
        result[cfg.timestamp_column] = pd.to_datetime(
            result[cfg.timestamp_column], errors="coerce", utc=True, format="mixed"
        )
        return result

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _unique_tx_count(self, df: pd.DataFrame, keys: str | list[str]) -> pd.Series:
        """Unique transactions per group (0 when the group key is missing)."""
        counts = df.groupby(keys)[self.config.transaction_column].transform("nunique")
        return counts.fillna(0).astype(int)

    @staticmethod
    def _unique_count(df: pd.DataFrame, key: str, target: str) -> pd.Series:
        """Distinct `target` values per `key` (0 when either is missing)."""
        counts = df.groupby(key)[target].transform("nunique")
        return counts.fillna(0).astype(int)

    def _seconds_since_previous_tx(self, df: pd.DataFrame) -> pd.DataFrame:
        """Per wallet, seconds since its previous distinct transaction."""
        cfg = self.config
        wallet, tx, ts = cfg.wallet_column, cfg.transaction_column, cfg.timestamp_column

        events = (
            df[[wallet, tx, ts]]
            .dropna(subset=[wallet, tx])
            .drop_duplicates([wallet, tx])
            .sort_values([wallet, ts])
        )
        events["_gap"] = events.groupby(wallet)[ts].diff().dt.total_seconds()
        events["_is_first"] = events.groupby(wallet).cumcount().eq(0)
        return df.merge(
            events[[wallet, tx, "_gap", "_is_first"]],
            on=[wallet, tx],
            how="left",
        )

    # ------------------------------------------------------------------ #
    # Extraction
    # ------------------------------------------------------------------ #
    def extract(self) -> pd.DataFrame:
        """Return one feature row per input observation (cached after first call)."""
        if self._features is None:
            features = self._compute_features()
            if self.graph_engine is not None:
                features = self._attach_graph_features(features)
            self._features = features
        return self._features.copy()

    def _attach_graph_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Left-join the per-transaction graph table onto the per-row features."""
        table = self.graph_engine.get_graph_feature_table()
        graph_columns = [c for c in table.columns if c != "transaction_id"]

        # many_to_one: several rows may share a transaction_id, but the graph
        # table must have exactly one row per transaction.
        merged = features.merge(table, on="transaction_id", how="left", validate="many_to_one")

        self._graph_unmatched_rows = int(merged[graph_columns[0]].isna().sum())
        merged[graph_columns] = merged[graph_columns].fillna(0).astype(int)
        return merged

    def _compute_features(self) -> pd.DataFrame:
        cfg = self.config
        df = self._seconds_since_previous_tx(self.data)
        out = pd.DataFrame(index=df.index)

        # ---- identifiers (standard names regardless of config) ----
        out["transaction_id"] = df[cfg.transaction_column]
        out["wallet_address"] = df[cfg.wallet_column]
        out["ip_address"] = df[cfg.ip_column]
        out["port_no"] = df[cfg.port_column]
        out["timestamp"] = df[cfg.timestamp_column]

        # ---- transaction features ----
        amount = df[cfg.amount_column]
        wallet_mean = amount.groupby(df[cfg.wallet_column]).transform("mean")
        ratio = (amount / wallet_mean).replace([float("inf"), float("-inf")], float("nan"))

        out["feature_btc_amount"] = amount.fillna(0.0)
        out["feature_amount_vs_wallet_mean"] = ratio.fillna(0.0)

        # ---- network features ----
        out["feature_ip_tx_count"] = self._unique_tx_count(df, cfg.ip_column)
        out["feature_port_tx_count"] = self._unique_tx_count(df, cfg.port_column)
        out["feature_wallet_tx_count"] = self._unique_tx_count(df, cfg.wallet_column)
        out["feature_ip_unique_wallets"] = self._unique_count(df, cfg.ip_column, cfg.wallet_column)
        out["feature_wallet_unique_ips"] = self._unique_count(df, cfg.wallet_column, cfg.ip_column)
        out["feature_ip_unique_ports"] = self._unique_count(df, cfg.ip_column, cfg.port_column)

        # ---- temporal features ----
        ts = df[cfg.timestamp_column]
        hour = ts.dt.hour
        weekday = ts.dt.dayofweek

        out["feature_hour"] = hour.fillna(MISSING_SENTINEL).astype(int)
        out["feature_day_of_week"] = weekday.fillna(MISSING_SENTINEL).astype(int)
        out["feature_is_night"] = hour.isin(NIGHT_HOURS).astype(int)
        out["feature_is_weekend"] = weekday.isin([5, 6]).astype(int)

        day = df.assign(_day=ts.dt.floor("D"))
        out["feature_ip_daily_tx_count"] = self._unique_tx_count(day, [cfg.ip_column, "_day"])

        out["feature_wallet_is_first_tx"] = df["_is_first"].fillna(False).astype(int)
        out["feature_wallet_seconds_since_prev_tx"] = df["_gap"].fillna(0.0)

        return out[list(self.ID_COLUMNS) + list(FEATURE_COLUMNS)]

    # ------------------------------------------------------------------ #
    # Outputs for the ML stage
    # ------------------------------------------------------------------ #
    @property
    def feature_names(self) -> list[str]:
        """All numeric feature columns (tabular + graph, when a graph engine is set)."""
        return [c for c in self.extract().columns if c.startswith("feature_")]

    def get_model_matrix(self) -> pd.DataFrame:
        """Numeric-only feature matrix (no identifiers), ready for sklearn."""
        return self.extract()[self.feature_names].astype(float)

    def get_feature_stats(self) -> dict[str, Any]:
        """Basic statistics and data-quality counters."""
        cfg = self.config
        features = self.extract()
        names = self.feature_names
        tx = self.data[cfg.transaction_column]

        groups = {
            "transaction": list(TRANSACTION_FEATURES),
            "network": list(NETWORK_FEATURES),
            "temporal": list(TEMPORAL_FEATURES),
        }
        if self.graph_engine is not None:
            groups["graph"] = [c for c in names if c.startswith("feature_graph_")]

        return {
            "rows": int(len(features)),
            "transactions": int(tx.nunique()),
            "feature_count": len(names),
            "feature_columns": names,
            "groups": groups,
            "data_quality": {
                "missing_transaction_ids": int(tx.isna().sum()),
                "missing_timestamps": int(self.data[cfg.timestamp_column].isna().sum()),
                "missing_amounts": int(self.data[cfg.amount_column].isna().sum()),
                "duplicate_transaction_ids": int(tx.dropna().duplicated().sum()),
                "rows_without_graph_features": self._graph_unmatched_rows,
            },
        }