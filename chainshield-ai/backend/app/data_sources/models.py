from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TransactionData:
    txid: str
    amount_btc: float
    fee_sats: float
    num_inputs: int
    num_outputs: int
    timestamp: Optional[int] = None
    source: str = "unknown"
    raw_features: dict = field(default_factory=dict)


@dataclass
class WalletData:
    address: str
    total_received_btc: float
    total_sent_btc: float
    tx_count: int
    connected_addresses: list = field(default_factory=list)
    source: str = "unknown"
