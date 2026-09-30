import networkx as nx
import pandas as pd

class GraphEngine:
    def __init__(self, edgelist_path="data/elliptic_txs_edgelist.csv"):
        self.edges_df = pd.read_csv(edgelist_path)
        self.graph = nx.from_pandas_edgelist(
            self.edges_df, source="txId1", target="txId2", create_using=nx.DiGraph()
        )

    def get_graph_risk(self, txid: str) -> dict:
        try:
            txid_int = int(txid)
        except ValueError:
            return {"graph_score": 0.0, "reason": "Invalid TXID format"}

        if txid_int not in self.graph:
            return {"graph_score": 0.0, "reason": "Transaction not present in edge graph"}

        in_degree = self.graph.in_degree(txid_int)
        out_degree = self.graph.out_degree(txid_int)

        raw_score = 0
        reasons = []

        if out_degree > 10:
            raw_score += 15
            reasons.append(f"high fan-out ({out_degree} outgoing links)")

        if in_degree > 10:
            raw_score += 10
            reasons.append(f"high fan-in ({in_degree} incoming links)")

        normalized_score = min(raw_score, 25) / 25

        reason_text = "Normal connectivity pattern" if not reasons else "; ".join(reasons)

        return {"graph_score": normalized_score, "reason": reason_text}
