CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS applicants (
    applicant_id TEXT PRIMARY KEY,
    consent_given BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS alt_data_signals (
    applicant_id TEXT REFERENCES applicants(applicant_id),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    recharge_freq_per_month REAL,
    recharge_regularity REAL,
    tenure_months_on_number REAL,
    utility_pct_on_time REAL,
    utility_avg_days_late REAL,
    txn_freq_per_month REAL,
    txn_regularity REAL,
    merchant_diversity REAL,
    platform_tenure_days REAL,
    kyc_complete BOOLEAN
);

-- Reference population for pgvector-based cohort similarity search
-- (model-service/model/db.py + model/embeddings.py). Deliberately NOT a
-- foreign key to `applicants`: this holds the synthetic training
-- population's embeddings + known outcomes (used to estimate a new
-- applicant's cold-start risk), which is a different, independent
-- population from real consented app users. Vector dimension (8) matches
-- EMBED_DIM in model-service/model/embeddings.py.
CREATE TABLE IF NOT EXISTS borrower_embeddings (
    applicant_id TEXT PRIMARY KEY,
    embedding vector(8),
    outcome BOOLEAN
);

CREATE TABLE IF NOT EXISTS score_history (
    id SERIAL PRIMARY KEY,
    applicant_id TEXT REFERENCES applicants(applicant_id),
    scored_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    risk_score REAL,
    method TEXT,
    explanation TEXT,
    result_json TEXT  -- full score response (incl. top_factors), stored as JSON text for simplicity
);
