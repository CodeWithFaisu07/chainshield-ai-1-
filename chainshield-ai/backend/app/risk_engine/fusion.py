import joblib
import numpy as np
import shap

MODEL_PATH = "app/models/random_forest.pkl"
ANOMALY_MODEL_PATH = "app/models/isolation_forest.pkl"

WEIGHTS = {
    "ai_classification": 0.40,
    "anomaly_detection": 0.25,
    "graph_behavior": 0.20,
    "rule_engine": 0.15,
}


class RiskEngine:
    def __init__(self, graph_engine=None):
        self.rf_model = joblib.load(MODEL_PATH)
        self.iso_model = joblib.load(ANOMALY_MODEL_PATH)
        self.explainer = shap.TreeExplainer(self.rf_model)
        self.graph_engine = graph_engine

    def score_offline_transaction(self, txid: str, raw_features: dict) -> dict:
        feature_names = list(raw_features.keys())
        X = np.array(list(raw_features.values())).reshape(1, -1)

        ml_prob = self.rf_model.predict_proba(X)[0][1]
        anomaly_raw = self.iso_model.decision_function(X)[0]
        anomaly_score = self._normalize_anomaly(anomaly_raw)

        ml_points = ml_prob * 100 * WEIGHTS["ai_classification"]
        anomaly_points = anomaly_score * 100 * WEIGHTS["anomaly_detection"]

        graph_points = 0
        graph_reason = None
        if self.graph_engine:
            graph_result = self.graph_engine.get_graph_risk(txid)
            graph_points = graph_result["graph_score"] * 100 * WEIGHTS["graph_behavior"]
            graph_reason = graph_result["reason"]

        total = ml_points + anomaly_points + graph_points

        top_reasons = self._get_shap_explanation(X, feature_names)

        return {
            "total_risk_score": round(total, 2),
            "path": "PATH_A_HISTORICAL_MODEL",
            "breakdown": {
                "ai_classification": round(ml_points, 2),
                "anomaly_detection": round(anomaly_points, 2),
                "graph_behavior": round(graph_points, 2),
            },
            "graph_reason": graph_reason,
            "explainability": {
                "top_contributing_features": top_reasons
            },
            "disclaimer": "Trained on Elliptic historical dataset - benchmark score, not live prediction",
        }

    def score_live_transaction(self, tx_features: dict) -> dict:
        score = 0
        reasons = []

        if tx_features["amount_btc"] > 0:
            fee_ratio = tx_features["fee_sats"] / (tx_features["amount_btc"] * 1e8)
            if fee_ratio > 0.05:
                score += 15
                reasons.append("Unusually high fee-to-amount ratio")

        if tx_features["num_outputs"] > 10:
            score += 20
            reasons.append(f"High output count ({tx_features['num_outputs']}) - possible splitting pattern")

        if tx_features["amount_btc"] > 10:
            score += 15
            reasons.append(f"Large transaction value ({tx_features['amount_btc']:.2f} BTC)")

        return {
            "total_risk_score": min(score, 100),
            "path": "PATH_B_LIVE_RULES",
            "reasons": reasons,
            "disclaimer": "Rule-based live scoring - not from Elliptic-trained ML model",
        }

    def _get_shap_explanation(self, X, feature_names, top_n=5):
        raw = self.explainer.shap_values(X)
        arr = np.array(raw)

        if isinstance(raw, list):
            values = np.array(raw[1][0])
        elif arr.ndim == 3:
            values = arr[0, :, 1]
        elif arr.ndim == 2:
            values = arr[0]
        else:
            values = arr

        values = np.ravel(values).astype(float)
        contributions = list(zip(feature_names, values))
        top = sorted(contributions, key=lambda x: abs(x[1]), reverse=True)[:top_n]
        return [{"feature": f"feature_{f}", "impact": round(float(v), 4)} for f, v in top]

    def _normalize_anomaly(self, raw_score: float) -> float:
        return max(0, min(1, (0.5 - raw_score)))
