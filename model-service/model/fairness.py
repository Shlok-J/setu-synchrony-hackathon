"""
Fairness audit over the trained model's own predictions. See DESIGN.md
section 3. Gender/region are never model features -- they're only here so
we can check the model's *output* for disparity across groups.
"""

import pandas as pd

from model.scoring import FEATURE_COLUMNS


def _group_approval_rates(df: pd.DataFrame, approved, column: str) -> dict:
    working = df.copy()
    working["_approved"] = approved
    return working.groupby(column)["_approved"].mean().round(4).to_dict()


def _disparity_ratio(rates: dict):
    values = list(rates.values())
    if not values or max(values) == 0:
        return None
    return round(min(values) / max(values), 4)


def compute_fairness_report(training_df: pd.DataFrame, engine) -> dict:
    X = engine.scaler.transform(training_df[FEATURE_COLUMNS])
    predicted_proba = engine.direct_model.predict_proba(X)[:, 1]
    approved = predicted_proba >= 0.5

    by_gender = _group_approval_rates(training_df, approved, "gender")
    by_region = _group_approval_rates(training_df, approved, "region")

    return {
        "overall_model_approval_rate": round(float(approved.mean()), 4),
        "by_gender": by_gender,
        "by_region": by_region,
        "disparity_ratio_gender": _disparity_ratio(by_gender),
        "disparity_ratio_region": _disparity_ratio(by_region),
        "note": (
            "Computed from the trained model's own predictions across the full "
            "training population -- this checks the model's output, not just "
            "the raw label balance. Gender/region are audit-only fields, never "
            "model inputs. A disparity ratio below 0.8 (the common 'four-fifths "
            "rule' threshold) would flag a group for review. This same check "
            "would run identically against real production outcomes."
        ),
    }
