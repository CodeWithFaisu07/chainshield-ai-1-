import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import joblib
import json
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

from app.data_sources.offline_source import OfflineEllipticSource


def train():
    print("Loading Elliptic dataset...")
    source = OfflineEllipticSource()
    X, y = source.get_training_data()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Training Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        class_weight="balanced",
        random_state=42,
    )
    rf.fit(X_train, y_train)

    y_pred = rf.predict(X_test)
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision_illicit": precision_score(y_test, y_pred),
        "recall_illicit": recall_score(y_test, y_pred),
        "f1_illicit": f1_score(y_test, y_pred),
    }
    print("Random Forest metrics:", metrics)

    print("Training Isolation Forest...")
    iso = IsolationForest(contamination=0.1, random_state=42)
    iso.fit(X_train)

    joblib.dump(rf, "app/models/random_forest.pkl")
    joblib.dump(iso, "app/models/isolation_forest.pkl")
    with open("app/models/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("Models saved: random_forest.pkl, isolation_forest.pkl")


if __name__ == "__main__":
    train()