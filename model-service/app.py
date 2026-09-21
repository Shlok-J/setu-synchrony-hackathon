"""
Setu model-service: the Python microservice that owns the actual ML.
Spring Boot calls this over HTTP; it never talks to applicants directly.

Run with:  uvicorn app:app --reload --port 8000   (from inside model-service/)
"""

import os
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

from model.db import connect as db_connect
from model.explain import generate_explanation
from model.fairness import compute_fairness_report
from model.scoring import SetuScoringEngine

app = FastAPI(title="Setu Model Service")

# default matches a plain repo checkout; the Docker image sets
# SYNTHETIC_DATA_PATH explicitly since its layout is different
DATA_PATH = Path(
    os.environ.get(
        "SYNTHETIC_DATA_PATH",
        str(Path(__file__).resolve().parent.parent / "data" / "synthetic_applicants.csv"),
    )
)
_training_df = pd.read_csv(DATA_PATH)

# None if Postgres isn't reachable -- engine just falls back to sklearn
_db_conn = db_connect()
engine = SetuScoringEngine(_training_df, db_conn=_db_conn)


class ScoreRequest(BaseModel):
    applicant_id: str
    days_active: int = 0
    recharge_freq_per_month: float = 0
    recharge_regularity: float = 0
    tenure_months_on_number: float = 0
    utility_pct_on_time: float = 0
    utility_avg_days_late: float = 0
    txn_freq_per_month: float = 0
    txn_regularity: float = 0
    merchant_diversity: float = 0
    platform_tenure_days: float = 0
    kyc_complete: int = 0


@app.get("/health")
def health():
    return {
        "status": "ok",
        "training_rows": len(_training_df),
        "pgvector_cohort_search": engine.db_conn is not None,
    }


@app.get("/fairness-report")
def fairness_report():
    return compute_fairness_report(_training_df, engine)


@app.post("/score")
def score(req: ScoreRequest):
    applicant = req.model_dump(exclude={"applicant_id", "days_active"})
    result = engine.score(applicant, days_active=req.days_active)
    explanation = generate_explanation(result.top_factors, result.method)
    return {
        "applicant_id": req.applicant_id,
        "risk_score": result.risk_score,
        "risk_band": _band(result.risk_score),
        "method": result.method,
        "cohort_weight": result.cohort_weight,
        "top_factors": result.top_factors,
        "explanation": explanation,
    }


def _band(value: float) -> str:
    if value >= 0.7:
        return "low_risk"
    if value >= 0.45:
        return "medium_risk"
    return "high_risk"
