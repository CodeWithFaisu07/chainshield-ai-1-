from collections import deque


class TraceEngine:
    def __init__(self, graph):
        self.graph = graph

    def trace_transaction(self, txid: str, depth: int = 2, limit: int = 50):
        try:
            start = int(txid)
        except ValueError:
            raise ValueError("Invalid TXID format")

        if start not in self.graph:
            raise ValueError("Transaction not present in trace graph")

        depth = max(1, min(depth, 5))
        limit = max(1, min(limit, 200))

        queue = deque([(start, 0)])
        visited = {start}

        nodes = [
            {
                "id": str(start),
                "depth": 0
            }
        ]

        edges = []
        edge_set = set()

        while queue and len(nodes) < limit:
            current, current_depth = queue.popleft()

            if current_depth >= depth:
                continue

            for neighbor in self.graph.successors(current):

                edge = (current, neighbor)

                if edge not in edge_set:
                    edge_set.add(edge)

                    edges.append({
                        "source": str(current),
                        "target": str(neighbor)
                    })

                if neighbor not in visited:

                    if len(nodes) >= limit:
                        break

                    visited.add(neighbor)

                    nodes.append({
                        "id": str(neighbor),
                        "depth": current_depth + 1
                    })

                    queue.append(
                        (neighbor, current_depth + 1)
                    )

        return {
            "start_txid": str(start),
            "depth": depth,
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "source": "elliptic_transaction_graph"
        }