from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

MAX_PORT = 65_535


@dataclass(frozen=True)
class CorrelationConfig:
    """Column mapping and normalization options for the SIH correlation engine."""

    transaction_column: str = "transaction_id"
    wallet_column: str = "wallet_address"
    ip_column: str = "ip_address"
    port_column: str = "port_no"
    timestamp_column: str = "timestamp"
    # Ethereum-style addresses are case-insensitive; Bitcoin (base58) ones are NOT.
    # Keep False unless your dataset is EVM-only.
    normalize_wallet_case: bool = False

    @property
    def required_columns(self) -> tuple[str, ...]:
        return (
            self.transaction_column,
            self.wallet_column,
            self.ip_column,
            self.port_column,
            self.timestamp_column,
        )


class TransactionNotFoundError(ValueError):
    """Raised when a transaction id does not exist in the dataset."""


class CorrelationEngine:
    """
    Correlates network-layer observations with blockchain-layer entities.

    Relationship model:  IP -> Transaction -> Wallet

    Important:
        An IP address is only a network observation. It is NOT proof of a
        person's identity (NAT, VPNs, Tor, proxies and shared Wi-Fi can put many
        people behind one IP, and one person behind many IPs).
    """

    def __init__(
        self,
        data: pd.DataFrame,
        config: CorrelationConfig | None = None,
    ) -> None:
        self.config = config or CorrelationConfig()
        self.data = self._validate_and_prepare(data)

        cfg = self.config
        self._indexes: dict[str, dict[str, list[int]]] = {
            column: self._build_index(column)
            for column in (cfg.transaction_column, cfg.ip_column, cfg.wallet_column)
        }

    # ------------------------------------------------------------------ #
    # Preparation
    # ------------------------------------------------------------------ #
    def _validate_and_prepare(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate the input and return a cleaned, independent working copy."""
        if not isinstance(data, pd.DataFrame):
            raise TypeError("data must be a pandas DataFrame")

        cfg = self.config
        missing = sorted(set(cfg.required_columns) - set(data.columns))
        if missing:
            raise ValueError(f"Correlation dataset is missing required columns: {missing}")
        if data.empty:
            raise ValueError("Correlation dataset cannot be empty")

        # reset_index guarantees positional index == label, so lookups are safe
        # even if the caller passed a filtered / duplicated / non-default index.
        result = data.copy().reset_index(drop=True)

        for column in (cfg.transaction_column, cfg.wallet_column, cfg.ip_column):
            result[column] = self._clean_string(result[column])

        if cfg.normalize_wallet_case:
            result[cfg.wallet_column] = result[cfg.wallet_column].str.lower()

        result[cfg.port_column] = self._clean_port(result[cfg.port_column])
        result[cfg.timestamp_column] = pd.to_datetime(
            result[cfg.timestamp_column], errors="coerce", utc=True
        )
        return result

    @staticmethod
    def _clean_string(series: pd.Series) -> pd.Series:
        """Strip whitespace and turn empty strings into proper missing values."""
        cleaned = series.astype("string").str.strip()
        return cleaned.mask((cleaned == "").fillna(False))

    @staticmethod
    def _clean_port(series: pd.Series) -> pd.Series:
        """Coerce to nullable int; anything invalid or outside 0-65535 becomes <NA>."""
        numeric = pd.to_numeric(series, errors="coerce")
        valid = numeric.notna() & (numeric % 1 == 0) & numeric.between(0, MAX_PORT)
        return numeric.where(valid).astype("Int64")

    def _build_index(self, column: str) -> dict[str, list[int]]:
        """Map each non-null value in `column` to the row positions where it occurs."""
        groups = self.data.groupby(column, sort=False, dropna=True).indices
        return {str(key): positions.tolist() for key, positions in groups.items()}

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _normalize_key(self, column: str, value: Any) -> str:
        key = str(value).strip()
        if column == self.config.wallet_column and self.config.normalize_wallet_case:
            key = key.lower()
        return key

    def _rows_for(self, column: str, value: Any) -> pd.DataFrame:
        key = self._normalize_key(column, value)
        return self.data.iloc[self._indexes[column].get(key, [])]

    @staticmethod
    def _unique_sorted(series: pd.Series) -> list[str]:
        return sorted(series.dropna().astype(str).unique().tolist())

    @staticmethod
    def _iso(timestamp: Any) -> str | None:
        return None if pd.isna(timestamp) else pd.Timestamp(timestamp).isoformat()

    def _transactions_of(self, column: str, value: Any) -> list[str]:
        rows = self._rows_for(column, value)
        return self._unique_sorted(rows[self.config.transaction_column])

    def _summarize_pairs(self, rows: pd.DataFrame) -> list[dict[str, Any]]:
        """Aggregate rows into (ip, wallet) relationships with evidence counts."""
        cfg = self.config
        if rows.empty:
            return []

        grouped = (
            rows.groupby([cfg.ip_column, cfg.wallet_column], dropna=True)
            .agg(
                transaction_count=(cfg.transaction_column, "nunique"),
                first_seen=(cfg.timestamp_column, "min"),
                last_seen=(cfg.timestamp_column, "max"),
            )
            .reset_index()
            .sort_values(
                ["transaction_count", cfg.ip_column, cfg.wallet_column],
                ascending=[False, True, True],
            )
        )

        return [
            {
                "ip_address": str(row[cfg.ip_column]),
                "wallet_address": str(row[cfg.wallet_column]),
                "transaction_count": int(row["transaction_count"]),
                "first_seen": self._iso(row["first_seen"]),
                "last_seen": self._iso(row["last_seen"]),
            }
            for row in grouped.to_dict("records")
        ]

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def get_transaction_links(self, transaction_id: str) -> dict[str, Any]:
        """Return network and wallet observations for one transaction."""
        cfg = self.config
        transaction_id = self._normalize_key(cfg.transaction_column, transaction_id)
        rows = self._rows_for(cfg.transaction_column, transaction_id)

        if rows.empty:
            raise TransactionNotFoundError(f"Transaction not found: {transaction_id}")

        timestamps = rows[cfg.timestamp_column].dropna().drop_duplicates().sort_values()

        return {
            "transaction_id": transaction_id,
            "ips": self._unique_sorted(rows[cfg.ip_column]),
            "wallets": self._unique_sorted(rows[cfg.wallet_column]),
            "ports": sorted(int(p) for p in rows[cfg.port_column].dropna().unique()),
            "timestamps": [self._iso(ts) for ts in timestamps],
        }

    def get_ip_transactions(self, ip_address: str) -> list[str]:
        """Return unique transactions observed from an IP address."""
        return self._transactions_of(self.config.ip_column, ip_address)

    def get_wallet_transactions(self, wallet_address: str) -> list[str]:
        """Return unique transactions associated with a wallet."""
        return self._transactions_of(self.config.wallet_column, wallet_address)

    def get_ip_wallet_links(self, ip_address: str) -> list[dict[str, Any]]:
        """Wallets observed through an IP, strongest evidence first."""
        return self._summarize_pairs(self._rows_for(self.config.ip_column, ip_address))

    def get_wallet_ip_links(self, wallet_address: str) -> list[dict[str, Any]]:
        """IPs observed for a wallet, strongest evidence first."""
        return self._summarize_pairs(
            self._rows_for(self.config.wallet_column, wallet_address)
        )

    def get_shared_ips(self, min_wallets: int = 2) -> list[dict[str, Any]]:
        """
        IPs linked to at least `min_wallets` different wallets.

        Treat as a lead, not proof: shared IPs are common (NAT, VPN, Tor, exchanges).
        """
        if min_wallets < 2:
            raise ValueError("min_wallets must be at least 2")

        cfg = self.config
        pairs = self.data[[cfg.ip_column, cfg.wallet_column]].dropna().drop_duplicates()
        wallets_per_ip = pairs.groupby(cfg.ip_column)[cfg.wallet_column].agg(
            lambda s: sorted(s.astype(str))
        )

        results = [
            {"ip_address": str(ip), "wallet_count": len(wallets), "wallets": wallets}
            for ip, wallets in wallets_per_ip.items()
            if len(wallets) >= min_wallets
        ]
        return sorted(results, key=lambda r: (-r["wallet_count"], r["ip_address"]))

    def get_stats(self) -> dict[str, int]:
        """Return high-level correlation statistics (missing values are not counted)."""
        cfg = self.config
        pairs = self.data[[cfg.ip_column, cfg.wallet_column]].dropna().drop_duplicates()

        return {
            "transactions": int(self.data[cfg.transaction_column].nunique()),
            "wallets": int(self.data[cfg.wallet_column].nunique()),
            "ips": int(self.data[cfg.ip_column].nunique()),
            "ports": int(self.data[cfg.port_column].nunique()),
            "ip_wallet_relationships": int(len(pairs)),
        }