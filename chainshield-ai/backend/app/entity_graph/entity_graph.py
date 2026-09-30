from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import cached_property
from typing import Any

import networkx as nx
import pandas as pd

MAX_PORT = 65_535


class NodeType:
    IP = "IP"
    TRANSACTION = "TRANSACTION"
    WALLET = "WALLET"


class Relationship:
    OBSERVED = "OBSERVED"  # IP -> TRANSACTION
    ASSOCIATED = "ASSOCIATED"  # TRANSACTION -> WALLET


# Prefixes used in node ids (kept short and collision-safe).
_ID_PREFIX = {
    NodeType.IP: "IP",
    NodeType.TRANSACTION: "TX",
    NodeType.WALLET: "WALLET",
}


# Graph-based feature names, defined once so the single-transaction API, the
# batch table and any downstream model code can never drift apart.
GRAPH_FEATURES = (
    "feature_graph_transaction_degree",    # distinct IPs + wallets touching the tx
    "feature_graph_ip_degree",             # distinct IPs that observed the tx
    "feature_graph_wallet_degree",         # distinct wallets associated with the tx
    "feature_graph_observation_count",     # raw edge count (repeat observations included)
    "feature_graph_max_ip_tx_count",       # busiest IP of this tx: how many txs it observed
    "feature_graph_max_wallet_tx_count",   # busiest wallet of this tx: how many txs it has
    "feature_graph_shared_ip_wallets",     # OTHER wallets reachable through this tx's IPs
    "feature_graph_related_transactions",  # OTHER txs sharing an IP or wallet with this tx
    "feature_graph_cluster_transactions",  # size of the connected cluster (txs)
    "feature_graph_cluster_wallets",       # size of the connected cluster (wallets)
)


@dataclass(frozen=True)
class EntityGraphConfig:
    """Configuration for the SIH entity graph."""

    transaction_column: str = "transaction_id"
    wallet_column: str = "wallet_address"
    ip_column: str = "ip_address"
    port_column: str = "port_no"
    timestamp_column: str = "timestamp"
    amount_column: str = "bitcoin_transferred"
    # Ethereum-style addresses are case-insensitive; Bitcoin (base58) ones are NOT.
    normalize_wallet_case: bool = False

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


class EntityNotFoundError(ValueError):
    """Raised when a requested entity does not exist in the graph."""


class EntityGraphEngine:
    """
    Builds an investigation graph from SIH network and blockchain data.

    Node types:  IP, TRANSACTION, WALLET
    Edge types:  OBSERVED    IP -> TRANSACTION
                 ASSOCIATED  TRANSACTION -> WALLET

    Design notes:
        * Rows with a missing transaction id are skipped; missing IP / wallet
          only skip that one edge (never create fake "nan" nodes).
        * Identical observations collapse into a single edge (deterministic
          edge keys), so re-loading the same data never inflates the graph.
        * Per-observation facts (port, amount, timestamp) live on edges, because
          one transaction can have many IPs / wallets.
        * IP addresses are observations, not identities. Clusters built through
          shared IPs are investigative leads, not proof (NAT, VPN, Tor).
    """

    def __init__(
        self,
        data: pd.DataFrame,
        config: EntityGraphConfig | None = None,
    ) -> None:
        self.config = config or EntityGraphConfig()
        self.data = self._validate_and_prepare(data)
        self.skipped_rows = 0
        self.graph = nx.MultiDiGraph()
        self._build_graph()

    # ------------------------------------------------------------------ #
    # Validation and cleaning
    # ------------------------------------------------------------------ #
    def _validate_and_prepare(self, data: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(data, pd.DataFrame):
            raise TypeError("data must be a pandas DataFrame")

        cfg = self.config
        missing = sorted(set(cfg.required_columns) - set(data.columns))
        if missing:
            raise ValueError(f"Entity graph dataset is missing required columns: {missing}")
        if data.empty:
            raise ValueError("Entity graph dataset cannot be empty")

        result = data.copy().reset_index(drop=True)

        for column in (cfg.transaction_column, cfg.wallet_column, cfg.ip_column):
            cleaned = result[column].astype("string").str.strip()
            result[column] = cleaned.mask((cleaned == "").fillna(False))

        if cfg.normalize_wallet_case:
            result[cfg.wallet_column] = result[cfg.wallet_column].str.lower()

        port = pd.to_numeric(result[cfg.port_column], errors="coerce")
        valid_port = port.notna() & (port % 1 == 0) & port.between(0, MAX_PORT)
        result[cfg.port_column] = port.where(valid_port).astype("Int64")

        amount = pd.to_numeric(result[cfg.amount_column], errors="coerce")
        result[cfg.amount_column] = amount.where(amount.map(pd.notna) & amount.abs().lt(float("inf")))

        result[cfg.timestamp_column] = pd.to_datetime(
            result[cfg.timestamp_column], errors="coerce", utc=True, format="mixed"
        )
        return result

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _normalize_value(self, node_type: str, value: Any) -> str:
        text = str(value).strip()
        if node_type == NodeType.WALLET and self.config.normalize_wallet_case:
            text = text.lower()
        return text

    def _node_id(self, node_type: str, value: Any) -> str:
        return f"{_ID_PREFIX[node_type]}:{self._normalize_value(node_type, value)}"

    @staticmethod
    def _iso(timestamp: Any) -> str | None:
        return None if pd.isna(timestamp) else pd.Timestamp(timestamp).isoformat()

    def _require_node(self, node_type: str, value: Any) -> str:
        node = self._node_id(node_type, value)
        if node not in self.graph:
            raise EntityNotFoundError(f"{node_type.title()} not found in graph: {value}")
        return node

    def _values_of(self, nodes: set[str] | list[str]) -> list[str]:
        return sorted(self.graph.nodes[node]["value"] for node in nodes)

    # ------------------------------------------------------------------ #
    # Graph construction
    # ------------------------------------------------------------------ #
    def _build_graph(self) -> None:
        cfg = self.config
        data = self.data

        # 1) Transaction nodes, with a time window aggregated over all their rows.
        windows = data.groupby(cfg.transaction_column, sort=False)[cfg.timestamp_column].agg(
            ["min", "max"]
        )
        for tx_id, window in windows.iterrows():
            self.graph.add_node(
                self._node_id(NodeType.TRANSACTION, tx_id),
                node_type=NodeType.TRANSACTION,
                value=str(tx_id),
                first_seen=self._iso(window["min"]),
                last_seen=self._iso(window["max"]),
            )

        # 2) Edges (and IP / wallet nodes) from each observation.
        rows = zip(
            data[cfg.transaction_column],
            data[cfg.ip_column],
            data[cfg.wallet_column],
            data[cfg.port_column],
            data[cfg.timestamp_column],
            data[cfg.amount_column],
        )

        for tx_id, ip, wallet, port, timestamp, amount in rows:
            if pd.isna(tx_id):
                self.skipped_rows += 1
                continue

            tx_node = self._node_id(NodeType.TRANSACTION, tx_id)
            ts = self._iso(timestamp)
            port_value = None if pd.isna(port) else int(port)
            amount_value = None if pd.isna(amount) else float(amount)

            if not pd.isna(ip):
                ip_node = self._node_id(NodeType.IP, ip)
                self.graph.add_node(ip_node, node_type=NodeType.IP, value=str(ip))
                self.graph.add_edge(
                    ip_node,
                    tx_node,
                    key=f"{Relationship.OBSERVED}|{ts}|{port_value}",
                    relationship=Relationship.OBSERVED,
                    port_no=port_value,
                    timestamp=ts,
                )

            if not pd.isna(wallet):
                wallet_node = self._node_id(NodeType.WALLET, wallet)
                self.graph.add_node(wallet_node, node_type=NodeType.WALLET, value=str(wallet))
                self.graph.add_edge(
                    tx_node,
                    wallet_node,
                    key=f"{Relationship.ASSOCIATED}|{ts}|{amount_value}",
                    relationship=Relationship.ASSOCIATED,
                    timestamp=ts,
                    bitcoin_transferred=amount_value,
                )

    # ------------------------------------------------------------------ #
    # Query API
    # ------------------------------------------------------------------ #
    def get_transaction_subgraph(self, transaction_id: str) -> dict[str, Any]:
        """Immediate IP and wallet relationships of one transaction."""
        tx_node = self._require_node(NodeType.TRANSACTION, transaction_id)
        nodes = {tx_node, *self.graph.predecessors(tx_node), *self.graph.successors(tx_node)}
        subgraph = self.graph.subgraph(nodes)
        return {
            "transaction_id": self._normalize_value(NodeType.TRANSACTION, transaction_id),
            "nodes": self._serialize_nodes(subgraph),
            "edges": self._serialize_edges(subgraph),
        }

    def get_ip_neighbors(self, ip_address: str) -> dict[str, Any]:
        """Transactions observed from an IP, and the wallets they touched."""
        ip_node = self._node_id(NodeType.IP, ip_address)
        if ip_node not in self.graph:
            return {"ip_address": ip_address, "transactions": [], "wallets": []}

        transactions = set(self.graph.successors(ip_node))
        wallets = {w for tx in transactions for w in self.graph.successors(tx)}
        return {
            "ip_address": ip_address,
            "transactions": self._values_of(transactions),
            "wallets": self._values_of(wallets),
        }

    def get_wallet_neighbors(self, wallet_address: str) -> dict[str, Any]:
        """Transactions associated with a wallet, and the IPs that observed them."""
        wallet_node = self._node_id(NodeType.WALLET, wallet_address)
        if wallet_node not in self.graph:
            return {"wallet_address": wallet_address, "transactions": [], "ips": []}

        transactions = set(self.graph.predecessors(wallet_node))
        ips = {i for tx in transactions for i in self.graph.predecessors(tx)}
        return {
            "wallet_address": wallet_address,
            "transactions": self._values_of(transactions),
            "ips": self._values_of(ips),
        }

    def get_entity_subgraph(
        self,
        node_type: str,
        value: str,
        radius: int = 2,
    ) -> dict[str, Any]:
        """
        Everything within `radius` hops (ignoring edge direction) of an entity.

        node_type is one of "IP", "TRANSACTION", "WALLET". Radius 2 from an IP
        gives its transactions and their wallets.
        """
        if node_type not in _ID_PREFIX:
            raise ValueError(f"node_type must be one of {sorted(_ID_PREFIX)}")
        if radius < 1:
            raise ValueError("radius must be at least 1")

        center = self._require_node(node_type, value)
        ego = nx.ego_graph(self.graph.to_undirected(as_view=True), center, radius=radius)
        subgraph = self.graph.subgraph(ego.nodes)
        return {
            "center": center,
            "radius": radius,
            "nodes": self._serialize_nodes(subgraph),
            "edges": self._serialize_edges(subgraph),
        }

    def get_clusters(self, min_transactions: int = 2) -> list[dict[str, Any]]:
        """
        Connected groups of entities, largest first.

        Clusters that join several transactions are worth a look, but a cluster
        bridged only by a shared IP is a lead, not proof of a common owner.
        """
        clusters: list[dict[str, Any]] = []

        for component in nx.weakly_connected_components(self.graph):
            by_type: dict[str, set[str]] = {t: set() for t in _ID_PREFIX}
            for node in component:
                by_type[self.graph.nodes[node]["node_type"]].add(node)

            if len(by_type[NodeType.TRANSACTION]) < min_transactions:
                continue

            clusters.append(
                {
                    "ips": self._values_of(by_type[NodeType.IP]),
                    "transactions": self._values_of(by_type[NodeType.TRANSACTION]),
                    "wallets": self._values_of(by_type[NodeType.WALLET]),
                }
            )

        clusters.sort(key=lambda c: (-len(c["transactions"]), c["transactions"]))
        return [{"cluster_id": i, **c} for i, c in enumerate(clusters, start=1)]

    # ------------------------------------------------------------------ #
    # Graph features (input for the ML stage)
    # ------------------------------------------------------------------ #
    @cached_property
    def _cluster_lookup(self) -> dict[str, tuple[int, int]]:
        """node -> (transactions, wallets) of its connected cluster. Built once.

        Assumes the graph is not modified after construction.
        """
        lookup: dict[str, tuple[int, int]] = {}
        for component in nx.weakly_connected_components(self.graph):
            types = Counter(self.graph.nodes[node]["node_type"] for node in component)
            size = (types[NodeType.TRANSACTION], types[NodeType.WALLET])
            for node in component:
                lookup[node] = size
        return lookup

    def _neighbors_of_type(self, nodes: Any, node_type: str) -> set[str]:
        return {n for n in nodes if self.graph.nodes[n].get("node_type") == node_type}

    def _graph_features_for_node(self, tx_node: str) -> dict[str, int]:
        graph = self.graph

        ips = self._neighbors_of_type(graph.predecessors(tx_node), NodeType.IP)
        wallets = self._neighbors_of_type(graph.successors(tx_node), NodeType.WALLET)

        # Transactions reachable through each of this tx's IPs / wallets.
        txs_via_ips = {t for ip in ips for t in graph.successors(ip)}
        txs_via_wallets = {t for w in wallets for t in graph.predecessors(w)}
        other_wallets = {w for t in txs_via_ips for w in graph.successors(t)} - wallets

        cluster_txs, cluster_wallets = self._cluster_lookup[tx_node]

        return {
            "feature_graph_transaction_degree": len(ips) + len(wallets),
            "feature_graph_ip_degree": len(ips),
            "feature_graph_wallet_degree": len(wallets),
            "feature_graph_observation_count": int(graph.degree(tx_node)),
            "feature_graph_max_ip_tx_count": max(
                (len(set(graph.successors(ip))) for ip in ips), default=0
            ),
            "feature_graph_max_wallet_tx_count": max(
                (len(set(graph.predecessors(w))) for w in wallets), default=0
            ),
            "feature_graph_shared_ip_wallets": len(other_wallets),
            "feature_graph_related_transactions": len(
                (txs_via_ips | txs_via_wallets) - {tx_node}
            ),
            "feature_graph_cluster_transactions": cluster_txs,
            "feature_graph_cluster_wallets": cluster_wallets,
        }

    def get_transaction_graph_features(self, transaction_id: str) -> dict[str, int]:
        """
        Graph-based numeric features for one transaction (see GRAPH_FEATURES).

        Degrees count DISTINCT neighbours, so repeated observations of the same
        IP or wallet do not inflate them (that count is kept separately in
        feature_graph_observation_count).
        """
        tx_node = self._require_node(NodeType.TRANSACTION, transaction_id)
        return self._graph_features_for_node(tx_node)

    def get_graph_feature_table(self) -> pd.DataFrame:
        """
        One row per transaction: `transaction_id` + every GRAPH_FEATURES column.

        Merge into the tabular features with:
            features.merge(table, on="transaction_id", how="left")
        """
        rows = [
            {"transaction_id": attrs["value"], **self._graph_features_for_node(node)}
            for node, attrs in self.graph.nodes(data=True)
            if attrs.get("node_type") == NodeType.TRANSACTION
        ]
        table = pd.DataFrame(rows, columns=["transaction_id", *GRAPH_FEATURES])
        return table.sort_values("transaction_id").reset_index(drop=True)

    # ------------------------------------------------------------------ #
    # Statistics
    # ------------------------------------------------------------------ #
    def get_stats(self) -> dict[str, int]:
        """Node and edge counts grouped by entity type."""
        nodes = Counter(attrs.get("node_type") for _, attrs in self.graph.nodes(data=True))
        edges = Counter(attrs.get("relationship") for *_, attrs in self.graph.edges(data=True))

        return {
            "ip_nodes": nodes[NodeType.IP],
            "transaction_nodes": nodes[NodeType.TRANSACTION],
            "wallet_nodes": nodes[NodeType.WALLET],
            "observed_edges": edges[Relationship.OBSERVED],
            "associated_edges": edges[Relationship.ASSOCIATED],
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "skipped_rows": self.skipped_rows,
        }

    # ------------------------------------------------------------------ #
    # Serialization (sorted, so output is deterministic)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _serialize_nodes(graph: nx.MultiDiGraph) -> list[dict[str, Any]]:
        return [
            {"id": node_id, **attributes}
            for node_id, attributes in sorted(graph.nodes(data=True), key=lambda n: n[0])
        ]

    @staticmethod
    def _serialize_edges(graph: nx.MultiDiGraph) -> list[dict[str, Any]]:
        edges = [
            {"source": source, "target": target, "key": key, **attributes}
            for source, target, key, attributes in graph.edges(keys=True, data=True)
        ]
        return sorted(edges, key=lambda e: (e["source"], e["target"], e["key"]))