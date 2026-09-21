"""
Sample applicant profiles across the spectrum, checking the model behaves
sensibly (direction and which path fires), not exact numbers -- cohort
matching has some natural variance run to run.
"""

import pandas as pd
import pytest

from model.scoring import SetuScoringEngine

EXCELLENT = {
    "recharge_freq_per_month": 9.5, "recharge_regularity": 0.86,
    "tenure_months_on_number": 44, "utility_pct_on_time": 0.90,
    "utility_avg_days_late": 2, "txn_freq_per_month": 23,
    "txn_regularity": 0.85, "merchant_diversity": 9,
    "platform_tenure_days": 330, "kyc_complete": 1,
}

POOR = {
    "recharge_freq_per_month": 4.6, "recharge_regularity": 0.54,
    "tenure_months_on_number": 16, "utility_pct_on_time": 0.55,
    "utility_avg_days_late": 14, "txn_freq_per_month": 7,
    "txn_regularity": 0.45, "merchant_diversity": 3,
    "platform_tenure_days": 90, "kyc_complete": 0,
}

AVERAGE = {
    "recharge_freq_per_month": 7, "recharge_regularity": 0.7,
    "tenure_months_on_number": 30, "utility_pct_on_time": 0.72,
    "utility_avg_days_late": 8, "txn_freq_per_month": 15,
    "txn_regularity": 0.65, "merchant_diversity": 6,
    "platform_tenure_days": 200, "kyc_complete": 1,
}

# Long tenure but currently-poor behavior -- deliberately inconsistent, to
# check the model weighs recent behavior over just "having been around".
INCONSISTENT = {
    "recharge_freq_per_month": 4.5, "recharge_regularity": 0.5,
    "tenure_months_on_number": 48, "utility_pct_on_time": 0.5,
    "utility_avg_days_late": 15, "txn_freq_per_month": 6,
    "txn_regularity": 0.4, "merchant_diversity": 3,
    "platform_tenure_days": 400, "kyc_complete": 1,
}


@pytest.fixture(scope="module")
def engine():
    df = pd.read_csv("../data/synthetic_applicants.csv")
    return SetuScoringEngine(df)


def test_excellent_profile_scores_low_risk_when_warm(engine):
    result = engine.score(EXCELLENT, days_active=90)
    assert result.method == "direct"
    assert result.risk_score >= 0.70, f"expected low risk, got {result.risk_score}"


def test_poor_profile_scores_high_risk_when_warm(engine):
    result = engine.score(POOR, days_active=90)
    assert result.method == "direct"
    assert result.risk_score <= 0.45, f"expected high risk, got {result.risk_score}"


def test_excellent_beats_poor_at_every_tenure_stage(engine):
    for days in [0, 3, 45, 90]:
        excellent = engine.score(EXCELLENT, days_active=days)
        poor = engine.score(POOR, days_active=days)
        assert excellent.risk_score > poor.risk_score, (
            f"at days_active={days}, excellent ({excellent.risk_score}) "
            f"should score above poor ({poor.risk_score})"
        )


def test_cold_start_uses_pure_cohort_method(engine):
    result = engine.score(AVERAGE, days_active=0)
    assert result.method == "cohort"
    assert result.cohort_weight == 1.0
    assert result.top_factors == []  # no per-factor breakdown in pure cohort mode


def test_exact_midpoint_is_a_true_50_50_blend(engine):
    result = engine.score(AVERAGE, days_active=45)
    assert result.method == "blended"
    assert result.cohort_weight == pytest.approx(0.5, abs=1e-9)


def test_near_cold_start_is_mostly_cohort_weighted(engine):
    result = engine.score(AVERAGE, days_active=3)
    assert result.method == "blended"
    assert result.cohort_weight > 0.9, "3 days in, the cohort estimate should still dominate"


def test_inconsistent_profile_still_produces_a_valid_score(engine):
    # Not asserting a direction here -- the point is just that a profile with
    # mismatched signals (long tenure, poor recent behavior) doesn't crash
    # and produces sensible top_factors to inspect manually.
    result = engine.score(INCONSISTENT, days_active=90)
    assert 0.0 <= result.risk_score <= 1.0
    assert len(result.top_factors) == 4
