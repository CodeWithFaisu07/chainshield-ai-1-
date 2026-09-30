from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".json", ".xml"}

class DatasetImportError(ValueError):
    """Raised when an investigation dataset cannot be imported."""


REQUIRED_COLUMNS = {
    "transaction_id",
    "wallet_address",
    "ip_address",
    "port_no",
    "timestamp",
    "bitcoin_transferred",
}


def load_dataset(file_path: str | Path) -> pd.DataFrame:
    """
    Load CSV, JSON or XML and normalize it into ChainShield's
    internal investigation-observation schema.

    Supported input styles include:
      - ChainShield native schema
      - sender/receiver transaction datasets
      - common alternative column names
    """
    path = Path(file_path)

    if not path.exists():
        raise DatasetImportError(f"Dataset file not found: {path}")

    if not path.is_file():
        raise DatasetImportError(f"Dataset path is not a file: {path}")

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise DatasetImportError(
            "Unsupported dataset format. "
            "Supported formats: CSV, JSON, XML."
        )

    try:
        if extension == ".csv":
            dataframe = pd.read_csv(path)

        elif extension == ".json":
            dataframe = _load_json(path)

        else:
            dataframe = pd.read_xml(path)

    except Exception as exc:
        raise DatasetImportError(
            f"Failed to parse {extension[1:].upper()} dataset: {exc}"
        ) from exc

    if not isinstance(dataframe, pd.DataFrame):
        raise DatasetImportError(
            "Imported dataset did not produce a valid table."
        )

    if dataframe.empty:
        raise DatasetImportError("Dataset contains no rows.")

    dataframe = _normalize_columns(dataframe)
    dataframe = _normalize_investigation_schema(dataframe)

    if dataframe.empty:
        raise DatasetImportError(
            "Dataset contains no valid transaction observations."
        )

    return dataframe


def _load_json(path: Path) -> pd.DataFrame:
    """
    Load common JSON dataset structures.

    Supported:
      1. Array of objects
      2. {"data": [...]}
      3. {"transactions": [...]}
    """
    try:
        with path.open("r", encoding="utf-8") as file:
            payload: Any = json.load(file)

    except json.JSONDecodeError as exc:
        raise DatasetImportError(
            f"Invalid JSON: {exc}"
        ) from exc

    if isinstance(payload, list):
        return pd.json_normalize(payload)

    if isinstance(payload, dict):
        for key in ("data", "transactions"):
            value = payload.get(key)

            if isinstance(value, list):
                return pd.json_normalize(value)

        return pd.json_normalize(payload)

    raise DatasetImportError(
        "JSON must contain an object or an array."
    )


def _normalize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    result = dataframe.copy()

    result.columns = [
        str(column).strip()
        for column in result.columns
    ]

    return result.reset_index(drop=True)


def _find_column(
    dataframe: pd.DataFrame,
    aliases: list[str],
) -> str | None:
    lookup = {
        str(column).strip().lower(): column
        for column in dataframe.columns
    }

    for alias in aliases:
        if alias.lower() in lookup:
            return lookup[alias.lower()]

    return None


def _normalize_investigation_schema(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    columns = {
        str(column).strip().lower()
        for column in dataframe.columns
    }

    # ---------------------------------------------------------
    # Already normalized ChainShield dataset
    # ---------------------------------------------------------

    if REQUIRED_COLUMNS.issubset(columns):
        result = dataframe.copy()

        result["transaction_id"] = (
            result["transaction_id"]
            .astype(str)
            .str.strip()
        )

        result["wallet_address"] = (
            result["wallet_address"]
            .astype(str)
            .str.strip()
        )

        result["ip_address"] = (
            result["ip_address"]
            .astype(str)
            .str.strip()
        )

        result["port_no"] = pd.to_numeric(
            result["port_no"],
            errors="coerce",
        )

        result["bitcoin_transferred"] = pd.to_numeric(
            result["bitcoin_transferred"],
            errors="coerce",
        )

        result["timestamp"] = pd.to_datetime(
            result["timestamp"],
            errors="coerce",
            utc=True,
        )

        result = result.dropna(
            subset=[
                "transaction_id",
                "wallet_address",
                "timestamp",
                "bitcoin_transferred",
            ]
        )

        return result.reset_index(drop=True)

    # ---------------------------------------------------------
    # Flexible sender/receiver investigation dataset
    # ---------------------------------------------------------

    tx_col = _find_column(
        dataframe,
        [
            "txid",
            "transaction_id",
            "transaction",
            "hash",
            "tx_hash",
        ],
    )

    timestamp_col = _find_column(
        dataframe,
        [
            "timestamp_utc",
            "timestamp",
            "time",
            "datetime",
            "date",
        ],
    )

    amount_col = _find_column(
        dataframe,
        [
            "amount_btc",
            "bitcoin_transferred",
            "btc_amount",
            "amount",
            "value_btc",
        ],
    )

    sender_wallet_col = _find_column(
        dataframe,
        [
            "sender_wallet",
            "sender_address",
            "from_wallet",
            "from_address",
            "source_wallet",
        ],
    )

    receiver_wallet_col = _find_column(
        dataframe,
        [
            "receiver_wallet",
            "receiver_address",
            "to_wallet",
            "to_address",
            "destination_wallet",
        ],
    )

    sender_ip_col = _find_column(
        dataframe,
        [
            "sender_ip",
            "source_ip",
            "from_ip",
        ],
    )

    receiver_ip_col = _find_column(
        dataframe,
        [
            "receiver_ip",
            "destination_ip",
            "to_ip",
        ],
    )

    source_port_col = _find_column(
        dataframe,
        [
            "source_port",
            "sender_port",
            "src_port",
        ],
    )

    destination_port_col = _find_column(
        dataframe,
        [
            "dest_port",
            "destination_port",
            "receiver_port",
            "dst_port",
        ],
    )

    missing = []

    if tx_col is None:
        missing.append("transaction ID")

    if timestamp_col is None:
        missing.append("timestamp")

    if amount_col is None:
        missing.append("BTC amount")

    if sender_wallet_col is None and receiver_wallet_col is None:
        missing.append("wallet address")

    if missing:
        raise DatasetImportError(
            "Unable to map required investigation fields: "
            + ", ".join(missing)
        )

    observations = []

    for _, row in dataframe.iterrows():

        txid = str(row[tx_col]).strip()

        if not txid or txid.lower() == "nan":
            continue

        timestamp = pd.to_datetime(
            row[timestamp_col],
            errors="coerce",
            utc=True,
        )

        amount = pd.to_numeric(
            row[amount_col],
            errors="coerce",
        )

        if pd.isna(timestamp) or pd.isna(amount):
            continue

        # -----------------------------------------------------
        # Sender observation
        # -----------------------------------------------------

        if sender_wallet_col is not None:
            wallet = str(
                row[sender_wallet_col]
            ).strip()

            ip = (
                str(row[sender_ip_col]).strip()
                if sender_ip_col is not None
                and pd.notna(row[sender_ip_col])
                else ""
            )

            port = (
                row[source_port_col]
                if source_port_col is not None
                else None
            )

            if wallet and wallet.lower() != "nan":

                observations.append(
                    {
                        "transaction_id": txid,
                        "wallet_address": wallet,
                        "ip_address": ip,
                        "port_no": pd.to_numeric(
                            port,
                            errors="coerce",
                        ),
                        "timestamp": timestamp,
                        "bitcoin_transferred": float(amount),
                        "entity_role": "sender",
                    }
                )

        # -----------------------------------------------------
        # Receiver observation
        # -----------------------------------------------------

        if receiver_wallet_col is not None:
            wallet = str(
                row[receiver_wallet_col]
            ).strip()

            ip = (
                str(row[receiver_ip_col]).strip()
                if receiver_ip_col is not None
                and pd.notna(row[receiver_ip_col])
                else ""
            )

            port = (
                row[destination_port_col]
                if destination_port_col is not None
                else None
            )

            if wallet and wallet.lower() != "nan":

                observations.append(
                    {
                        "transaction_id": txid,
                        "wallet_address": wallet,
                        "ip_address": ip,
                        "port_no": pd.to_numeric(
                            port,
                            errors="coerce",
                        ),
                        "timestamp": timestamp,
                        "bitcoin_transferred": float(amount),
                        "entity_role": "receiver",
                    }
                )

    result = pd.DataFrame(observations)

    if result.empty:
        raise DatasetImportError(
            "No valid sender/receiver transaction observations "
            "could be created from the dataset."
        )

    return result.reset_index(drop=True)