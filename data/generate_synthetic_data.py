"""
Synthetic alt-data applicant generator for Setu.

Generates a population of "underbanked" applicants with alternative-data
behavioral features plus a repayment outcome, driven by a single latent
"financial_discipline" factor + noise. Gender and region are generated
INDEPENDENTLY of that latent factor on purpose, so any disparity the
fairness audit finds later is something the model introduced, not
something baked into the ground truth.

Deliberately excludes: social-media/social-graph data, caste/religion,
granular location -- see DESIGN.md for why.
"""

from pathlib import Path

import numpy as np
import pandas as pd

RNG_SEED = 42
N_APPLICANTS = 4000


def generate(n=N_APPLICANTS, seed=RNG_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Latent, unobserved "financial discipline" factor in [0, 1].
    discipline = rng.beta(a=2.0, b=2.0, size=n)

    # --- Alt-data features, each correlated with `discipline` + its own noise ---
    recharge_freq_per_month = np.clip(rng.normal(4 + 6 * discipline, 1.5, n), 0, None)
    recharge_regularity = np.clip(rng.normal(0.5 + 0.4 * discipline, 0.15, n), 0, 1)
    tenure_months_on_number = np.clip(rng.normal(12 + 36 * discipline, 10, n), 1, None)

    utility_pct_on_time = np.clip(rng.normal(0.5 + 0.45 * discipline, 0.15, n), 0, 1)
    utility_avg_days_late = np.clip(rng.normal(15 - 14 * discipline, 5, n), 0, None)

    txn_freq_per_month = np.clip(rng.normal(5 + 20 * discipline, 5, n), 0, None)
    txn_regularity = np.clip(rng.normal(0.4 + 0.5 * discipline, 0.15, n), 0, 1)
    merchant_diversity = np.clip(rng.normal(2 + 8 * discipline, 2, n), 1, None)

    platform_tenure_days = np.clip(rng.normal(60 + 300 * discipline, 90, n), 1, None)
    kyc_complete = rng.binomial(1, np.clip(0.5 + 0.4 * discipline, 0, 1))

    # --- Fields used ONLY for the fairness audit, independent of discipline ---
    gender = rng.choice(["female", "male", "other"], size=n, p=[0.48, 0.48, 0.04])
    region = rng.choice(["urban", "semi_urban", "rural"], size=n, p=[0.35, 0.35, 0.30])

    # --- Outcome: driven by discipline + independent noise, NOT by gender/region ---
    logit = -2.5 + 5.5 * discipline + rng.normal(0, 0.6, n)
    prob_repaid = 1 / (1 + np.exp(-logit))
    repaid_on_time = rng.binomial(1, prob_repaid)

    df = pd.DataFrame({
        "applicant_id": [f"APP{100000 + i}" for i in range(n)],
        "recharge_freq_per_month": recharge_freq_per_month,
        "recharge_regularity": recharge_regularity,
        "tenure_months_on_number": tenure_months_on_number,
        "utility_pct_on_time": utility_pct_on_time,
        "utility_avg_days_late": utility_avg_days_late,
        "txn_freq_per_month": txn_freq_per_month,
        "txn_regularity": txn_regularity,
        "merchant_diversity": merchant_diversity,
        "platform_tenure_days": platform_tenure_days,
        "kyc_complete": kyc_complete,
        "gender": gender,   # audit-only, never a model feature
        "region": region,   # audit-only, never a model feature
        "repaid_on_time": repaid_on_time,
    })
    return df


if __name__ == "__main__":
    data = generate()
    out_path = Path(__file__).resolve().parent / "synthetic_applicants.csv"
    data.to_csv(out_path, index=False)
    print(f"Wrote {len(data)} rows to {out_path}")
    print(data.head())
    print("\nOverall repayment rate:", round(data["repaid_on_time"].mean(), 3))
    print("\nRepayment rate by gender (should be close across groups):")
    print(data.groupby("gender")["repaid_on_time"].mean().round(3))
    print("\nRepayment rate by region (should be close across groups):")
    print(data.groupby("region")["repaid_on_time"].mean().round(3))
