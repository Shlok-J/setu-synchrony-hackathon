"""
Setu model-service: the Python microservice that owns the actual ML.
Spring Boot calls this over HTTP; it never talks to applicants directly.

Run with:  uvicorn app:app --reload --port 8000   (from inside model-service/)
"""

from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Request
from pydantic import BaseModel

from model.explain import generate_explanation
from model.scoring import SetuScoringEngine

app = FastAPI(title="Setu Model Service")

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "synthetic_applicants.csv"
_training_df = pd.read_csv(DATA_PATH)
engine = SetuScoringEngine(_training_df)


@app.middleware("http")
async def log_score_requests(request: Request, call_next):
    # TEMPORARY diagnostic: the Spring Boot -> model-service hop has been
    # producing "body: Field required, input: null" despite two different
    # fixes on the Java side. Log exactly what actually arrives on the wire
    # so we stop guessing. Remove once this is resolved.
    if request.url.path == "/score":
        raw_body = await request.body()
        print(
            f"[DEBUG /score] method={request.method} "
            f"content-type={request.headers.get('content-type')!r} "
            f"content-length={request.headers.get('content-length')!r} "
            f"transfer-encoding={request.headers.get('transfer-encoding')!r} "
            f"body={raw_body!r}",
            flush=True,
        )
    return await call_next(request)


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
    return {"status": "ok", "training_rows": len(_training_df)}


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
