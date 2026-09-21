CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS applicants (
    applicant_id TEXT PRIMARY KEY,
    consent_given BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- reference population for the pgvector cohort search, not a foreign key
-- to applicants -- this is the synthetic training population, not real
-- app users. Vector dimension (8) matches EMBED_DIM in embeddings.py.
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
    result_json TEXT  -- full score response, stored as JSON text since top_factors is a list
);
