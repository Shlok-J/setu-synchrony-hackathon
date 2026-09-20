package com.synchrony.setu.dto;

// Field names are snake_case on purpose -- they mirror the frontend's JSON
// payload and the Python model-service's Pydantic model exactly, so Jackson
// needs no naming-strategy configuration on either side of this hop.
public record ApplicantScoreRequest(
        String applicant_id,
        int days_active,
        double recharge_freq_per_month,
        double recharge_regularity,
        double tenure_months_on_number,
        double utility_pct_on_time,
        double utility_avg_days_late,
        double txn_freq_per_month,
        double txn_regularity,
        double merchant_diversity,
        double platform_tenure_days,
        int kyc_complete
) {}
