import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from model.scoring import FEATURE_COLUMNS, SetuScoringEngine


def _toy_training_df(n=200):
    rng = np.random.default_rng(0)
    discipline = rng.beta(2, 2, n)
    df = pd.DataFrame({col: rng.normal(discipline, 0.2) for col in FEATURE_COLUMNS})
    df["kyc_complete"] = rng.binomial(1, 0.6, n)
    df["repaid_on_time"] = rng.binomial(1, discipline)
    return df


def test_cold_start_returns_valid_score_with_no_factors():
    engine = SetuScoringEngine(_toy_training_df())
    applicant = {col: 0.5 for col in FEATURE_COLUMNS}
    result = engine.score(applicant, days_active=0)
    assert result.method == "cohort"
    assert 0.0 <= result.risk_score <= 1.0
    assert result.top_factors == []


def test_warm_returns_factors_and_uses_direct_model():
    engine = SetuScoringEngine(_toy_training_df())
    applicant = {col: 0.8 for col in FEATURE_COLUMNS}
    result = engine.score(applicant, days_active=90)
    assert result.method == "direct"
    assert 0.0 <= result.risk_score <= 1.0
    assert len(result.top_factors) == 4


def test_mid_tenure_blends_between_cohort_and_direct():
    engine = SetuScoringEngine(_toy_training_df())
    applicant = {col: 0.6 for col in FEATURE_COLUMNS}
    result = engine.score(applicant, days_active=45)
    assert result.method == "blended"
    assert 0.0 < result.cohort_weight < 1.0
