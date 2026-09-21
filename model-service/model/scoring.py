"""
Blends a cohort-similarity cold-start estimate with a direct model, weighted
by how much history the applicant has. See DESIGN.md section 2.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

FEATURE_COLUMNS = [
    "recharge_freq_per_month",
    "recharge_regularity",
    "tenure_months_on_number",
    "utility_pct_on_time",
    "utility_avg_days_late",
    "txn_freq_per_month",
    "txn_regularity",
    "merchant_diversity",
    "platform_tenure_days",
    "kyc_complete",
]


@dataclass
class ScoreResult:
    risk_score: float          # 0-1, higher = more creditworthy
    method: str                # "cohort", "blended", or "direct"
    cohort_weight: float
    top_factors: list = field(default_factory=list)  # [{feature, direction, magnitude}, ...]


class SetuScoringEngine:
    def __init__(self, training_df: pd.DataFrame, k_neighbors: int = 25, db_conn=None):
        self.scaler = StandardScaler()
        X = self.scaler.fit_transform(training_df[FEATURE_COLUMNS])
        y = training_df["repaid_on_time"].to_numpy()

        # also doubles as the fallback if pgvector isn't available
        self._cohort_k = min(k_neighbors, len(training_df))
        self.cohort_index = NearestNeighbors(n_neighbors=self._cohort_k)
        self.cohort_index.fit(X)
        self._cohort_outcomes = y

        self.direct_model = GradientBoostingClassifier(
            n_estimators=150, max_depth=3, learning_rate=0.08, random_state=42
        )
        self.direct_model.fit(X, y)

        # optional pgvector lookup -- any failure here just leaves db_conn
        # as None and _cohort_score falls back to the sklearn index
        self.db_conn = None
        self.embedding_model = None
        if db_conn is not None:
            try:
                from model.embeddings import EmbeddingModel
                from model.db import populate_borrower_embeddings

                self.embedding_model = EmbeddingModel(X)
                populate_borrower_embeddings(
                    db_conn,
                    training_df["applicant_id"].tolist(),
                    self.embedding_model.embed_batch(X),
                    y,
                )
                self.db_conn = db_conn
            except Exception:
                self.db_conn = None
                self.embedding_model = None

    def _cohort_score(self, x_scaled: np.ndarray) -> float:
        if self.db_conn is not None and self.embedding_model is not None:
            try:
                from model.db import query_cohort_outcomes

                query_embedding = self.embedding_model.embed(x_scaled)
                outcomes = query_cohort_outcomes(self.db_conn, query_embedding, self._cohort_k)
                if outcomes:
                    return float(np.mean(outcomes))
            except Exception:
                pass  # fall through to sklearn

        _, idx = self.cohort_index.kneighbors(x_scaled.reshape(1, -1))
        return float(self._cohort_outcomes[idx[0]].mean())

    def _direct_score(self, x_scaled: np.ndarray) -> float:
        return float(self.direct_model.predict_proba(x_scaled.reshape(1, -1))[0, 1])

    def _top_factors(self, x_scaled: np.ndarray, n=4):
        # how much does the prediction move if we set each feature back to
        # the population mean (0 in standardized space) one at a time?
        # same idea as SHAP, just cheaper -- real SHAP is the upgrade path
        base = self._direct_score(x_scaled)
        impacts = []
        for i, col in enumerate(FEATURE_COLUMNS):
            perturbed = x_scaled.copy()
            perturbed[i] = 0.0
            shifted = self._direct_score(perturbed)
            impacts.append((col, base - shifted))
        impacts.sort(key=lambda t: abs(t[1]), reverse=True)
        return [
            {
                "feature": c,
                "direction": "positive" if v >= 0 else "negative",
                "magnitude": round(abs(v), 4),
            }
            for c, v in impacts[:n]
        ]

    def score(self, applicant: dict, days_active: int) -> ScoreResult:
        row = pd.DataFrame([{c: applicant.get(c, 0) for c in FEATURE_COLUMNS}])
        x_scaled = self.scaler.transform(row)[0]

        cohort = self._cohort_score(x_scaled)
        direct = self._direct_score(x_scaled)
        w = min(1.0, days_active / 90.0)  # 90 days = fully warmed up, chosen as a round number
        blended = (1 - w) * cohort + w * direct

        method = "cohort" if w == 0 else ("direct" if w == 1 else "blended")
        factors = self._top_factors(x_scaled) if w > 0 else []

        return ScoreResult(
            risk_score=round(float(blended), 4),
            method=method,
            cohort_weight=round(1 - w, 4),
            top_factors=factors,
        )
