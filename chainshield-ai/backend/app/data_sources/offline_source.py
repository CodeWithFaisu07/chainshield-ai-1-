import pandas as pd
from .models import TransactionData

FEATURES_PATH = "data/elliptic_txs_features.csv"
CLASSES_PATH = "data/elliptic_txs_classes.csv"


class OfflineEllipticSource:
    def __init__(self):
        self.features_df = pd.read_csv(FEATURES_PATH, header=None)
        self.classes_df = pd.read_csv(CLASSES_PATH)
        self.classes_df.columns = ["txId", "class"]

    def get_transaction_by_id(self, txid: str) -> TransactionData:
        row = self.features_df[self.features_df[0] == int(txid)]
        if row.empty:
            raise ValueError(f"Transaction {txid} not found in Elliptic dataset")

        feature_values = row.iloc[0, 2:].to_dict()

        return TransactionData(
            txid=str(txid),
            amount_btc=0.0,
            fee_sats=0.0,
            num_inputs=0,
            num_outputs=0,
            source="offline",
            raw_features=feature_values,
        )

    def get_training_data(self):
        merged = self.features_df.merge(
            self.classes_df, left_on=0, right_on="txId"
        )
        labeled = merged[merged["class"] != "unknown"]
        X = labeled.iloc[:, 2:167]
        y = labeled["class"].map({"1": 1, "2": 0})
        return X, y
