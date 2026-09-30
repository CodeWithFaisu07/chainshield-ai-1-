

from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile


from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.api.auth import router as auth_router

from app.data_sources.offline_source import OfflineEllipticSource
from app.data_sources.sih_source import SIHDataSource
from app.database import init_db
from app.dataset_analysis.importer import load_dataset
from app.entity_graph.entity_graph import EntityGraphEngine
from app.feature_engine.feature_extractor import FeatureExtractionEngine
from app.graph_engine.centrality import GraphEngine
from app.graph_engine.trace import TraceEngine
from app.risk_engine.fusion import RiskEngine
from app.risk_engine.sih_risk_fusion import SIHRiskFusion
from app.explainability.sih_explainer import SIHExplainer
from app.explainability.sih_shap_explainer import SIHSHAPExplainer
from scripts.train_sih_isolation_forest import (
    DEFAULT_MODEL_PATH,
    load_sih_isolation_forest,
)

logger = logging.getLogger("chainshield.api")

Mode = Literal["offline", "live", "sih"]
VALID_MODES = ("offline", "live", "sih")


# ----------------------------------------------------------------------
# Response models
# ----------------------------------------------------------------------

class ModeResponse(BaseModel):
    current_mode: Mode


class HealthResponse(BaseModel):
    status: str
    mode: Mode


class WalletResponse(BaseModel):
    address: str
    total_received_btc: float
    total_sent_btc: float
    tx_count: int
    source: str


class SihTransactionResponse(BaseModel):
    transaction_id: str
    mode: Literal["sih"]

    risk_score: float
    anomaly_score: float
    raw_anomaly_score: float
    is_anomaly: bool

    model: str
    feature_count: int

    observation_count: int
    ips: list[str]
    wallets: list[str]

    evidence: list[dict]
    disclaimer: str


class SihWalletResponse(BaseModel):
    wallet_address: str
    mode: Literal["sih"]
    transactions: list[str]
    ips: list[str]


# ----------------------------------------------------------------------
# Application state
# ----------------------------------------------------------------------

@dataclass
class OfflineComponents:
    source: OfflineEllipticSource
    graph_engine: GraphEngine
    risk_engine: RiskEngine
    trace_engine: TraceEngine


@dataclass
class SihComponents:
    data_source: SIHDataSource
    graph_engine: EntityGraphEngine
    feature_engine: FeatureExtractionEngine
    features: "object"
    model_artifact: dict
    risk_fusion: SIHRiskFusion


class AppState:
    def __init__(self) -> None:
        self.mode: Mode = "sih"

        
        self.offline: OfflineComponents | None = None
        self.sih: SihComponents | None = None

        self._lock = threading.Lock()

    
    def get_offline(self) -> OfflineComponents:
        with self._lock:
            if self.offline is None:
                logger.info(
                    "Loading offline Elliptic dataset and risk engine..."
                )

                source = OfflineEllipticSource()
                graph_engine = GraphEngine()

                self.offline = OfflineComponents(
                    source=source,
                    graph_engine=graph_engine,
                    risk_engine=RiskEngine(
                        graph_engine=graph_engine
                    ),
                    trace_engine=TraceEngine(
                        graph_engine.graph
                    ),
                )

            return self.offline

    def get_sih(
        self,
        model_path: Path = DEFAULT_MODEL_PATH,
    ) -> SihComponents:

        with self._lock:
            if self.sih is None:
                logger.info(
                    "Loading SIH dataset, graph, feature engine, "
                    "model and risk fusion..."
                )

                # ------------------------------------------------------
                # 1. Load SIH dataset
                # ------------------------------------------------------
                data_source = SIHDataSource()

                data = data_source.get_all_transactions()

                # ------------------------------------------------------
                # 2. Build entity graph
                # ------------------------------------------------------
                graph_engine = EntityGraphEngine(data)

                # ------------------------------------------------------
                # 3. Build feature engine
                # ------------------------------------------------------
                feature_engine = FeatureExtractionEngine(
                    data,
                    graph_engine=graph_engine,
                )

                features = feature_engine.extract()

                # ------------------------------------------------------
                # 4. Load trained SIH Isolation Forest
                # ------------------------------------------------------
                model_artifact = load_sih_isolation_forest(
                    model_path
                )

                # ------------------------------------------------------
                # 5. Initialize SIH Risk Fusion
                # ------------------------------------------------------
                risk_fusion = SIHRiskFusion(
                    model_path
                )

                # ------------------------------------------------------
                # 6. Store all SIH components
                # ------------------------------------------------------
                self.sih = SihComponents(
                    data_source=data_source,
                    graph_engine=graph_engine,
                    feature_engine=feature_engine,
                    features=features,
                    model_artifact=model_artifact,
                    risk_fusion=risk_fusion,
                )

            return self.sih


# ----------------------------------------------------------------------
# Error helpers
# ----------------------------------------------------------------------

def not_found(detail: str) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail=detail,
    )


def unavailable(
    mode: str,
    exc: Exception,
) -> HTTPException:

    logger.exception(
        "Failed to initialize %s components",
        mode,
    )

    return HTTPException(
        status_code=503,
        detail=f"{mode} mode is unavailable: {exc}",
    )


# ----------------------------------------------------------------------
# Application lifecycle
# ----------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    init_db()

    app.state.chainshield = AppState()

    yield

    # No teardown needed.
    # Current sources/engines hold no external connections to close.


def get_state(request: Request) -> AppState:

    if not hasattr(
        request.app.state,
        "chainshield",
    ):
        request.app.state.chainshield = AppState()

    return request.app.state.chainshield


# ----------------------------------------------------------------------
# FastAPI application
# ----------------------------------------------------------------------

app = FastAPI(
    title="ChainShield AI",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"],
)


# ----------------------------------------------------------------------
# Mode endpoints
# ----------------------------------------------------------------------

@app.post(
    "/mode/{mode}",
    response_model=ModeResponse,
)
def set_mode(
    mode: str,
    request: Request,
):

    app_state = get_state(request)

    if mode not in VALID_MODES:
        raise HTTPException(
            400,
            f"mode must be one of {VALID_MODES}",
        )

    if mode == "offline":

        try:
            app_state.get_offline()

        except Exception as exc:
            raise unavailable(
                "offline",
                exc,
            ) from exc

    elif mode == "sih":

        try:
            app_state.get_sih()

        except FileNotFoundError as exc:
            raise HTTPException(
                503,
                "No trained SIH model found. "
                "Run the training script first. "
                f"({exc})",
            ) from exc

        except Exception as exc:
            raise unavailable(
                "sih",
                exc,
            ) from exc

    app_state.mode = mode  # type: ignore[assignment]

    return ModeResponse(
        current_mode=app_state.mode
    )


@app.get(
    "/mode",
    response_model=ModeResponse,
)
def get_mode(request: Request):

    return ModeResponse(
        current_mode=get_state(request).mode
    )


@app.get(
    "/health",
    response_model=HealthResponse,
)
def health(request: Request):

    return HealthResponse(
        status="ok",
        mode=get_state(request).mode,
    )
# ----------------------------------------------------------------------
# Dataset import
# ----------------------------------------------------------------------

@app.post("/datasets/import")
async def import_dataset(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(
            400,
            "Dataset filename is required",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in {".csv", ".json", ".xml"}:
        raise HTTPException(
            400,
            "Unsupported dataset format. "
            "Supported formats: CSV, JSON, XML.",
        )

    upload_dir = Path("data") / "imports"
    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = upload_dir / file.filename

    try:
        contents = await file.read()
        destination.write_bytes(contents)

        # --------------------------------------------------
        # 1. IMPORT + NORMALIZE
        # --------------------------------------------------
        dataframe = load_dataset(destination)

        # --------------------------------------------------
        # 2. BUILD ENTITY GRAPH
        # --------------------------------------------------
        graph_engine = EntityGraphEngine(dataframe)
        graph_stats = graph_engine.get_stats()

        # --------------------------------------------------
        # 3. EXTRACT FEATURES
        # --------------------------------------------------
        feature_engine = FeatureExtractionEngine(
            dataframe,
            graph_engine=graph_engine,
        )

        features = feature_engine.extract()

        # --------------------------------------------------
        # 4. LOAD EXISTING SIH TRAINED MODEL
        # --------------------------------------------------
        model_artifact = load_sih_isolation_forest(
            DEFAULT_MODEL_PATH
        )

        feature_names = model_artifact["feature_names"]

        missing_features = sorted(
            set(feature_names) - set(features.columns)
        )

        if missing_features:
            raise HTTPException(
                500,
                (
                    "Uploaded dataset is incompatible with "
                    "the trained SIH model. Missing features: "
                    f"{missing_features}"
                ),
            )

        # --------------------------------------------------
        # 5. CREATE ONE REPRESENTATIVE ROW PER TRANSACTION
        # --------------------------------------------------
        transaction_features = (
            features[
                ["transaction_id"] + feature_names
            ]
            .copy()
        )

        transaction_features[feature_names] = (
            transaction_features[feature_names]
            .astype(float)
        )

        transaction_features = (
            transaction_features
            .groupby(
                "transaction_id",
                as_index=False,
            )[feature_names]
            .mean()
        )

        # --------------------------------------------------
        # 6. RISK FUSION
        # --------------------------------------------------
        risk_fusion = SIHRiskFusion(
            DEFAULT_MODEL_PATH
        )

        feature_frame = transaction_features[
            feature_names
        ]

        scores = risk_fusion.score_batch(
            feature_frame
        )

        # --------------------------------------------------
        # 7. EXPLAINABILITY
        # --------------------------------------------------
        explainer = SIHExplainer()

        shap_explainer = SIHSHAPExplainer(
            risk_fusion.model
        )

        alerts = []

        for transaction_id, score in zip(
            transaction_features["transaction_id"],
            scores,
        ):

            transaction_rows = features[
                features["transaction_id"]
                == transaction_id
            ]

            alert = {
                "transaction_id": str(
                    transaction_id
                ),

                "risk_score": float(
                    score["risk_score"]
                ),

                "anomaly_score": float(
                    score["anomaly_score"]
                ),

                "raw_anomaly_score": float(
                    score["raw_anomaly_score"]
                ),

                "is_anomaly": bool(
                    score["is_anomaly"]
                ),

                "model": str(
                    score["model"]
                ),

                "ips": sorted(
                    transaction_rows[
                        "ip_address"
                    ]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                ),

                "wallets": sorted(
                    transaction_rows[
                        "wallet_address"
                    ]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                ),

                "observation_count": int(
                    len(transaction_rows)
                ),

                "evidence": score[
                    "evidence"
                ],

                "explanations": explainer.explain(
                    score["evidence"]
                ),

                "disclaimer": str(
                    score.get(
                        "disclaimer",
                        (
                            "Anomaly scores are "
                            "investigative signals "
                            "and are not proof of "
                            "malicious or illegal activity."
                        ),
                    )
                ),
            }

            # SHAP only for anomalous transactions.
            if bool(score["is_anomaly"]):
                shap_result = shap_explainer.explain(
                    transaction_rows[
                        feature_names
                    ]
                    .mean()
                    .to_frame()
                    .T,
                    feature_names,
                    top_k=5,
                )

                alert["shap_explanations"] = (
                    shap_result
                )
            else:
                alert["shap_explanations"] = []

            alerts.append(alert)

        # --------------------------------------------------
        # 8. HIGHEST-RISK FIRST
        # --------------------------------------------------
        alerts.sort(
            key=lambda item: item["risk_score"],
            reverse=True,
        )

        anomalous_signals = sum(
            1
            for alert in alerts
            if alert["is_anomaly"]
        )

        # --------------------------------------------------
        # 9. FINAL ANALYSIS RESULT
        # --------------------------------------------------
        return {
            "status": "analysis_complete",

            "filename": file.filename,

            "total_rows": int(
                len(dataframe)
            ),

            "transactions_analyzed": int(
                len(transaction_features)
            ),

            "anomalous_signals": int(
                anomalous_signals
            ),

            "ip_entities": int(
                graph_stats["ip_nodes"]
            ),

            "wallet_entities": int(
                graph_stats["wallet_nodes"]
            ),

            "transaction_entities": int(
                graph_stats["transaction_nodes"]
            ),

            "observed_edges": int(
                graph_stats["observed_edges"]
            ),

            "associated_edges": int(
                graph_stats["associated_edges"]
            ),

            "graph": graph_stats,

            "model": {
                "name": "SIH Isolation Forest",
                "feature_count": int(
                    len(feature_names)
                ),
                "training_rows": model_artifact.get(
                    "training_rows"
                ),
                "contamination": model_artifact.get(
                    "contamination"
                ),
            },

            "alerts": alerts,

            "disclaimer": (
                "Anomaly and risk scores are "
                "investigative signals. They do not "
                "constitute proof of malicious or "
                "illegal activity."
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            400,
            f"Dataset analysis failed: {exc}",
        ) from exc



# ----------------------------------------------------------------------
# Transaction analysis
# ----------------------------------------------------------------------

@app.get(
    "/analyze/transaction/{txid}"
)
def analyze_transaction(
    txid: str,
    request: Request,
):

    app_state = get_state(request)



    if app_state.mode == "offline":
        return _analyze_offline_transaction(
            txid,
            app_state,
        )

    if app_state.mode == "sih":
        return _analyze_sih_transaction(
            txid,
            app_state,
        )

    raise HTTPException(
    400,
    "Transaction analysis is available only in OFFLINE or SIH mode",
)

    


# ----------------------------------------------------------------------
# Offline transaction analysis
# ----------------------------------------------------------------------

def _analyze_offline_transaction(
    txid: str,
    app_state: AppState,
) -> dict:

    try:
        offline = app_state.get_offline()

    except Exception as exc:
        raise unavailable(
            "offline",
            exc,
        ) from exc

    try:
        tx = offline.source.get_transaction_by_id(
            txid
        )

    except (KeyError, ValueError) as exc:
        raise not_found(
            f"Transaction not found: {txid}"
        ) from exc

    result = offline.risk_engine.score_offline_transaction(
        txid,
        tx.raw_features,
    )

    return {
        "txid": txid,
        "mode": "offline",
        **result,
    }





# ----------------------------------------------------------------------
# SIH transaction analysis
# ----------------------------------------------------------------------

def _analyze_sih_transaction(
    txid: str,
    app_state: AppState,
) -> SihTransactionResponse:

    try:
        sih = app_state.get_sih()

    except FileNotFoundError as exc:
        raise HTTPException(
            503,
            f"No trained SIH model found: {exc}",
        ) from exc

    except Exception as exc:
        raise unavailable(
            "sih",
            exc,
        ) from exc

    # --------------------------------------------------------------
    # Find transaction in feature dataset
    # --------------------------------------------------------------

    rows = sih.features[
        sih.features["transaction_id"] == txid
    ]

    if rows.empty:
        raise not_found(
            f"Transaction not found in SIH dataset: {txid}"
        )

    # --------------------------------------------------------------
    # Validate model/feature compatibility
    # --------------------------------------------------------------

    feature_names = sih.model_artifact[
        "feature_names"
    ]

    missing = set(feature_names) - set(rows.columns)

    if missing:
        raise HTTPException(
            500,
            (
                "SIH model is out of sync with the "
                "feature engine "
                f"(missing: {sorted(missing)}). "
                "Retrain the model."
            ),
        )

    # --------------------------------------------------------------
    # Build representative transaction feature row
    # --------------------------------------------------------------
    #
    # A transaction may have multiple observations.
    #
    # We use the mean of its model features so that one
    # observation/IP does not arbitrarily dominate the result.
    # --------------------------------------------------------------

    feature_row = (
        rows[feature_names]
        .astype(float)
        .mean(axis=0)
    )

    # --------------------------------------------------------------
    # SIH Risk Fusion
    # --------------------------------------------------------------

    result = sih.risk_fusion.score_transaction(
        feature_row
    )

    # --------------------------------------------------------------
    # Return complete SIH investigation result
    # --------------------------------------------------------------

    return SihTransactionResponse(
        transaction_id=txid,
        mode="sih",

        risk_score=float(
            result["risk_score"]
        ),

        anomaly_score=float(
            result["anomaly_score"]
        ),

        raw_anomaly_score=float(
            result["raw_anomaly_score"]
        ),

        is_anomaly=bool(
            result["is_anomaly"]
        ),

        model=str(
            result["model"]
        ),

        feature_count=int(
            result["feature_count"]
        ),

        observation_count=len(rows),

        ips=sorted(
            rows["ip_address"]
            .dropna()
            .unique()
            .tolist()
        ),

        wallets=sorted(
            rows["wallet_address"]
            .dropna()
            .unique()
            .tolist()
        ),

        evidence=result["evidence"],

        disclaimer=str(
            result["disclaimer"]
        ),
    )


# ----------------------------------------------------------------------
# Wallet analysis
# ----------------------------------------------------------------------

@app.get(
    "/analyze/wallet/{address}"
)
def analyze_wallet(
    address: str,
    request: Request,
):

    app_state = get_state(request)

    # --------------------------------------------------------------
    # SIH wallet analysis
    # --------------------------------------------------------------

    if app_state.mode == "sih":

        try:
            sih = app_state.get_sih()

        except Exception as exc:
            raise unavailable(
                "sih",
                exc,
            ) from exc

        neighbors = sih.graph_engine.get_wallet_neighbors(
            address
        )

        if not neighbors["transactions"]:
            raise not_found(
                f"Wallet not found in SIH dataset: {address}"
            )

        return SihWalletResponse(
            mode="sih",
            **neighbors,
        )

    # --------------------------------------------------------------
    # Non-SIH wallet analysis
    # --------------------------------------------------------------


# ----------------------------------------------------------------------
# Transaction trace
# ----------------------------------------------------------------------
@app.get(
    "/graph/sih/transaction/{txid}"
)
def get_sih_transaction_graph(
    txid: str,
    request: Request,
):
    app_state = get_state(request)

    if app_state.mode != "sih":
        raise HTTPException(
            400,
            "SIH transaction graph requires SIH mode",
        )

    try:
        sih = app_state.get_sih()

    except Exception as exc:
        raise unavailable(
            "sih",
            exc,
        ) from exc

    try:
        graph = sih.graph_engine.get_transaction_subgraph(
            txid
        )

    except Exception as exc:
        raise HTTPException(
            404,
            f"Transaction graph not found: {txid}",
        ) from exc

    return graph






@app.get(
    "/trace/transaction/{txid}"
)
def trace_transaction(
    txid: str,
    request: Request,
    depth: int = Query(
        2,
        ge=1,
        le=6,
        description="Hops to follow from the transaction",
    ),
    limit: int = Query(
        50,
        ge=1,
        le=500,
        description="Max nodes to return",
    ),
):

    app_state = get_state(request)

    if app_state.mode != "offline":
        raise HTTPException(
            400,
            "Transaction trace currently requires OFFLINE mode",
        )

    try:
        offline = app_state.get_offline()

    except Exception as exc:
        raise unavailable(
            "offline",
            exc,
        ) from exc

    try:
        return offline.trace_engine.trace_transaction(
            txid,
            depth=depth,
            limit=limit,
        )

    except ValueError as exc:
        raise not_found(
            str(exc)
        ) from exc


# ----------------------------------------------------------------------
# Live feed
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# SIH ranked investigative alerts
# ----------------------------------------------------------------------

@app.get(
    "/alerts/sih"
)
def get_sih_alerts(
    request: Request,
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Number of highest-risk investigative alerts",
    ),
):

    app_state = get_state(request)

    if app_state.mode != "sih":
        raise HTTPException(
            400,
            "Ranked SIH alerts require SIH mode",
        )

    try:
        sih = app_state.get_sih()

    except Exception as exc:
        raise unavailable(
            "sih",
            exc,
        ) from exc

    # --------------------------------------------------------------
    # Validate model/feature compatibility
    # --------------------------------------------------------------

    feature_names = sih.model_artifact[
        "feature_names"
    ]

    missing = set(feature_names) - set(
        sih.features.columns
    )

    if missing:
        raise HTTPException(
            500,
            (
                "SIH model is out of sync with the "
                "feature engine "
                f"(missing: {sorted(missing)}). "
                "Retrain the model."
            ),
        )

    # --------------------------------------------------------------
    # Score all SIH transactions in one batch
    # --------------------------------------------------------------

    rows = sih.features[
        ["transaction_id"] + feature_names
    ].copy()

    feature_frame = rows[
        feature_names
    ].astype(float)

    scores = sih.risk_fusion.score_batch(
        feature_frame
    )

    # --------------------------------------------------------------
    # Attach transaction IDs
    # --------------------------------------------------------------

    alerts = []
    explainer = SIHExplainer()
    shap_explainer = SIHSHAPExplainer(
    sih.risk_fusion.model
)



    for transaction_id, score in zip(
        rows["transaction_id"],
        scores,
    ):
        transaction_rows = sih.features[
            sih.features["transaction_id"]
            == transaction_id
        ]

        alerts.append(
            {
                "transaction_id": str(
                    transaction_id
                ),
                "risk_score": float(
                    score["risk_score"]
                ),
                "anomaly_score": float(
                    score["anomaly_score"]
                ),
                "raw_anomaly_score": float(
                    score["raw_anomaly_score"]
                ),
                "is_anomaly": bool(
                    score["is_anomaly"]
                ),
                "model": str(
                    score["model"]
                ),
                "ips": sorted(
                    transaction_rows[
                        "ip_address"
                    ]
                    .dropna()
                    .unique()
                    .tolist()
                ),
                "wallets": sorted(
                    transaction_rows[
                        "wallet_address"
                    ]
                    .dropna()
                    .unique()
                    .tolist()
                ),
                "observation_count": int(
                    len(transaction_rows)
                ),
                "evidence": score[
                    "evidence"
                ],
                "explanations": explainer.explain(
    score["evidence"]
),

"shap_explanations": shap_explainer.explain(
    transaction_rows[
        feature_names
    ].mean()
    .to_frame()
    .T,
    feature_names,
    top_k=5,
),
                "disclaimer": str(
                    score["disclaimer"]
                ),
            }
        )

    # --------------------------------------------------------------
    # Rank highest-risk transactions first
    # --------------------------------------------------------------

    alerts.sort(
        key=lambda item: item["risk_score"],
        reverse=True,
    )

    # --------------------------------------------------------------
    # Return requested number of alerts
    # --------------------------------------------------------------

    return {
        "mode": "sih",
        "model": "SIH Isolation Forest",
        "total_transactions_analyzed": len(
            alerts
        ),
        "returned_alerts": min(
            limit,
            len(alerts),
        ),
        "alerts": alerts[:limit],
    }

