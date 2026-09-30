import ipaddress
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)

# Is file ko backend/ ke andar rakhne ki assumption hai.
# Agar location alag hai to BASE_DIR adjust kar lena.
BASE_DIR = Path(__file__).resolve().parent


DATASET_PATH = BASE_DIR.parents[1] / "data" / "bitcoin_synthetic_dataset.csv"
MAX_FILE_SIZE_MB = 100


class SIHDataSource:
    REQUIRED_COLUMNS = [
        "transaction_id",
        "wallet_address",
        "ip_address",
        "port_no",
        "timestamp",
        "bitcoin_transferred",
    ]
    STRING_COLUMNS = ["transaction_id", "wallet_address", "ip_address"]

    def __init__(
        self,
        dataset_path: Union[str, Path] = DATASET_PATH,
        max_file_size_mb: int = MAX_FILE_SIZE_MB,
    ):
        self.dataset_path = Path(dataset_path).resolve()
        self.max_file_size_mb = max_file_size_mb
        self.data: Optional[pd.DataFrame] = None
        self._by_id: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def load(self) -> pd.DataFrame:
        self._check_file()

        raw = pd.read_csv(
            self.dataset_path,
            dtype={col: "string" for col in self.STRING_COLUMNS},
        )

        self._validate_columns(raw)
        self.data = self._preprocess(raw)
        self._by_id = self.data.set_index("transaction_id", drop=False)

        logger.info(
            "Loaded %d transactions from %s",
            len(self.data),
            self.dataset_path.name,
        )
        return self.data.copy()

    def _check_file(self) -> None:
        # Full path sirf log mein, exception message mein sirf file name
        if not self.dataset_path.is_file():
            logger.error("Dataset not found: %s", self.dataset_path)
            raise FileNotFoundError(
                f"SIH dataset not found: {self.dataset_path.name}"
            )

        size_mb = self.dataset_path.stat().st_size / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            raise ValueError(
                f"Dataset too large: {size_mb:.1f} MB "
                f"(limit {self.max_file_size_mb} MB)"
            )

    def _validate_columns(self, df: pd.DataFrame) -> None:
        missing = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]

        
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    # ------------------------------------------------------------------
    # Preprocessing
    # ------------------------------------------------------------------
    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        initial_rows = len(df)

        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["port_no"] = pd.to_numeric(df["port_no"], errors="coerce")
        df["bitcoin_transferred"] = pd.to_numeric(
            df["bitcoin_transferred"], errors="coerce"
        )

        for col in self.STRING_COLUMNS:
            df[col] = df[col].str.strip()

        # 1. Null values
        df = df.dropna(subset=self.REQUIRED_COLUMNS)
        after_null = len(df)

        # 2. Empty strings
        df = df[(df[self.STRING_COLUMNS] != "").all(axis=1)]

        # 3. Invalid IP addresses
        valid_ips = {
            ip for ip in df["ip_address"].unique() if self._is_valid_ip(ip)
        }
        df = df[df["ip_address"].isin(valid_ips)]

        # 4. Port: whole number in 0-65535
        df = df[
            df["port_no"].between(0, 65535)
            & (df["port_no"] == df["port_no"].round())
        ]

        # 5. Negative amounts
        df = df[df["bitcoin_transferred"] >= 0]
        after_validation = len(df)

        # 6. Duplicate transaction IDs (pehla rakho)
        df = df.drop_duplicates(subset="transaction_id", keep="first")
        after_dedup = len(df)

        df["port_no"] = df["port_no"].astype(int)
        df = df.reset_index(drop=True)

        dropped = initial_rows - len(df)
        if dropped:
            logger.warning(
                "Dropped %d/%d rows (null: %d, invalid values: %d, "
                "duplicate IDs: %d)",
                dropped,
                initial_rows,
                initial_rows - after_null,
                after_null - after_validation,
                after_validation - after_dedup,
            )

        return df

    @staticmethod
    def _is_valid_ip(value: str) -> bool:
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def _ensure_loaded(self) -> None:
        if self.data is None:
            self.load()

    def get_all_transactions(self) -> pd.DataFrame:
        self._ensure_loaded()
        # Copy taaki caller original data modify na kar sake
        return self.data.copy()

    def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        self._ensure_loaded()

        # Index lookup: O(1), full scan nahi
        try:
            row = self._by_id.loc[str(transaction_id).strip()]
        except KeyError:
            raise ValueError(
                f"Transaction not found: {transaction_id}"
            ) from None

        return row.to_dict()

    def get_stats(self) -> Dict[str, Any]:
        self._ensure_loaded()

        if self.data.empty:
            return {
                "total_transactions": 0,
                "unique_wallets": 0,
                "unique_ips": 0,
                "unique_ports": 0,
                "date_min": None,
                "date_max": None,
            }

        return {
            "total_transactions": int(len(self.data)),
            "unique_wallets": int(self.data["wallet_address"].nunique()),
            "unique_ips": int(self.data["ip_address"].nunique()),
            "unique_ports": int(self.data["port_no"].nunique()),
            "date_min": str(self.data["timestamp"].min()),
            "date_max": str(self.data["timestamp"].max()),
        }