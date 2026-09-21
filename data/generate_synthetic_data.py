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

Distribution shapes: count/duration-like features (recharge frequency,
tenure, transaction frequency, merchant diversity, days late) use Gamma
distributions -- the standard choice for positive, right-skewed behavioral
data, and naturally non-negative without an artificial clip-at-zero pile-up.
Rate/percentage features (regularity, on-time %) use Beta distributions --
the standard choice for bounded [0,1] proportions. Every feature's MEAN is
unchanged from the original clipped-Gaussian version (still a simple linear
function of `discipline`), so the model's already-validated behavior
(fairness ratios, blend mechanics) doesn't shift -- only the realistic
shape of the spread around that mean does.
"""

from pathlib import Path

import numpy as np
import pandas as pd

RNG_SEED = 42
N_APPLICANTS = 4000


def _gamma_around_mean(rng, mean, shape=4.0):
    """Gamma-distributed values with the given per-row mean and a fixed shape
    (higher shape = tighter/less skewed around the mean)."""
    mean = np.clip(mean, 1e-3, None)  # Gamma needs a strictly positive mean
    return rng.gamma(shape=shape, scale=mean / shape)


def _beta_around_mean(rng, mean, concentration=20.0):
    """Beta-distributed values in [0, 1] with the given per-row mean."""
    mean = np.clip(mean, 1e-3, 1 - 1e-3)
    alpha = mean * concentration
    beta = (1 - mean) * concentration
    return rng.beta(alpha, beta)


def generate(n=N_APPLICANTS, seed=RNG_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Latent, unobserved "financial discipline" factor in [0, 1].
    discipline = rng.beta(a=2.0, b=2.0, size=n)

    # --- Alt-data features, each correlated with `discipline` + realistic noise shape ---
    recharge_freq_per_month = _gamma_around_mean(rng, 4 + 6 * discipline, shape=5)
    recharge_regularity = _beta_around_mean(rng, 0.5 + 0.4 * discipline, concentration=20)
    tenure_months_on_number = np.round(_gamma_around_mean(rng, 12 + 36 * discipline, shape=4))

    utility_pct_on_time = _beta_around_mean(rng, 0.5 + 0.45 * discipline, concentration=20)
    utility_avg_days_late = _gamma_around_mean(rng, 15 - 14 * discipline, shape=4)

    txn_freq_per_month = _gamma_around_mean(rng, 5 + 20 * discipline, shape=5)
    txn_regularity = _beta_around_mean(rng, 0.4 + 0.5 * discipline, concentration=15)
    merchant_diversity = np.clip(np.round(_gamma_around_mean(rng, 2 + 8 * discipline, shape=4)), 1, None)

    platform_tenure_days = np.round(_gamma_around_mean(rng, 60 + 300 * discipline, shape=4))
    kyc_complete = rng.binomial(1, np.clip(0.5 + 0.4 * discipline, 0, 1))

    # --- Fields used ONLY for the fairness audit, independent of discipline ---
    gender = rng.choice(["female", "male", "other"], size=n, p=[0.48, 0.48, 0.04])
    region = rng.choice(["urban", "semi_urban", "rural"], size=n, p=[0.35, 0.35, 0.30])

    # --- Outcome: driven by discipline + independent noise, NOT by gender/region ---
    # (Unchanged: outcome depends on discipline directly, not on the specific
    # feature realizations above, so this distributional-shape change has no
    # effect on the fairness audit's independence property.)
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
    print("\nFeature distribution shapes (skew should now be > 0 for count-like features):")
    from scipy.stats import skew
    for col in ["recharge_freq_per_month", "txn_freq_per_month", "merchant_diversity", "utility_avg_days_late"]:
        print(f"  {col}: skew={skew(data[col]):.2f}, min={data[col].min():.2f}")
