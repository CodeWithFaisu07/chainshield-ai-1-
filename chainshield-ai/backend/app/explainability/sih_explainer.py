from __future__ import annotations

from typing import Any, Mapping


FEATURE_LABELS: dict[str, str] = {
    "feature_btc_amount": "Bitcoin transaction amount",
    "feature_ip_tx_count": "Observed IP transaction activity",
    "feature_port_tx_count": "Observed port transaction activity",
    "feature_wallet_tx_count": "Wallet transaction activity",
    "feature_is_night": "Night-time activity",
    "feature_graph_related_transactions": "Related graph transactions",
    "feature_graph_cluster_transactions": "Graph cluster activity",

    "feature_amount_vs_wallet_mean": "Amount compared with wallet average",
    "feature_ip_unique_wallets": "Unique wallets observed from IP",
    "feature_wallet_unique_ips": "Unique IPs associated with wallet",
    "feature_ip_unique_ports": "Unique ports observed from IP",
    "feature_hour": "Transaction hour",
    "feature_day_of_week": "Day of week",
    "feature_is_weekend": "Weekend activity",
    "feature_ip_daily_tx_count": "Daily IP transaction activity",
    "feature_wallet_is_first_tx": "First transaction for wallet",
    "feature_wallet_seconds_since_prev_tx": "Time since previous wallet transaction",
    "feature_graph_max_ip_tx_count": "Maximum IP activity in graph",
    "feature_graph_max_wallet_tx_count": "Maximum wallet activity in graph",
}



class SIHExplainer:
    """
    Converts model evidence into human-readable investigative reasons.

    This is an explanation layer, not a maliciousness classifier.
    """

    def explain(
        self,
        evidence: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        explanations: list[dict[str, Any]] = []

        for item in evidence:
            feature = str(item.get("feature", ""))
            value = item.get("value")

            label = FEATURE_LABELS.get(
                feature,
                feature.replace("_", " ").strip().title(),
            )

            reason = self._build_reason(
                feature,
                value,
            )

            explanations.append(
                {
                    "feature": feature,
                    "label": label,
                    "value": value,
                    "reason": reason,
                }
            )

        return explanations

    @staticmethod
    def _build_reason(
        feature: str,
        value: Any,
    ) -> str:

        if feature == "feature_btc_amount":
            return (
                f"Transaction transferred {value} BTC."
            )

        if feature == "feature_ip_tx_count":
            return (
                f"The observed IP is associated with "
                f"{value} transaction observations."
            )

        if feature == "feature_port_tx_count":
            return (
                f"The observed port appears in "
                f"{value} transaction observations."
            )

        if feature == "feature_wallet_tx_count":
            return (
                f"The wallet is associated with "
                f"{value} transaction observations."
            )

        if feature == "feature_is_night":
            if int(value) == 1:
                return (
                    "The transaction occurred during the "
                    "configured night-time period."
                )

            return (
                "The transaction did not occur during the "
                "configured night-time period."
            )

        if feature == "feature_graph_related_transactions":
            return (
                f"The entity graph contains "
                f"{value} related transaction observations."
            )

        if feature == "feature_graph_cluster_transactions":
            return (
                f"The transaction belongs to a graph cluster "
                f"containing {value} transaction observations."
            )

        return (
            f"The model received a value of {value} "
            f"for this feature."
        )