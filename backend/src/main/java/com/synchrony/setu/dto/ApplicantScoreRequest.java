package com.synchrony.setu.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;

// Field names are snake_case on purpose -- they mirror the frontend's JSON
// payload and the Python model-service's Pydantic model exactly, so Jackson
// needs no naming-strategy configuration on either side of this hop.
public record ApplicantScoreRequest(
        @NotBlank String applicant_id,
        @Min(0) int days_active,
        @Min(0) double recharge_freq_per_month,
        @Min(0) double recharge_regularity,
        @Min(0) double tenure_months_on_number,
        @Min(0) double utility_pct_on_time,
        @Min(0) double utility_avg_days_late,
        @Min(0) double txn_freq_per_month,
        @Min(0) double txn_regularity,
        @Min(0) double merchant_diversity,
        @Min(0) double platform_tenure_days,
        @Min(0) int kyc_complete
) {}
