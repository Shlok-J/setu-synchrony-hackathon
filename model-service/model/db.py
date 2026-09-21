"""
Postgres/pgvector connectivity for cohort similarity search.

connect() returns None instead of raising if Postgres isn't reachable, so
scoring.py can fall back to its scikit-learn lookup instead of crashing.
"""

import os

import psycopg2
import psycopg2.extras


def connect():
    """Returns a live connection, or None if Postgres isn't reachable."""
    try:
        conn = psycopg2.connect(
            host=os.environ.get("PGHOST", "localhost"),
            port=os.environ.get("PGPORT", "5432"),
            dbname=os.environ.get("PGDATABASE", "setu"),
            user=os.environ.get("PGUSER", "setu"),
            password=os.environ.get("PGPASSWORD", "setu_dev_password"),
            connect_timeout=5,
        )
        conn.autocommit = True
        return conn
    except Exception:
        return None


def _to_vector_literal(vec) -> str:
    # pgvector's text input format, e.g. '[0.1,0.2,0.3]'
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"


def populate_borrower_embeddings(conn, applicant_ids, embeddings, outcomes):
    """Idempotent: a no-op if the table already has rows."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM borrower_embeddings")
        (count,) = cur.fetchone()
        if count > 0:
            return count

        rows = [
            (aid, _to_vector_literal(emb), bool(outcome))
            for aid, emb, outcome in zip(applicant_ids, embeddings, outcomes)
        ]
        psycopg2.extras.execute_values(
            cur,
            "INSERT INTO borrower_embeddings (applicant_id, embedding, outcome) "
            "VALUES %s ON CONFLICT (applicant_id) DO NOTHING",
            rows,
            template="(%s, %s::vector, %s)",
        )
        return len(rows)


def query_cohort_outcomes(conn, query_embedding, k: int):
    """Nearest-k outcomes by pgvector Euclidean distance."""
    vec_literal = _to_vector_literal(query_embedding)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT outcome FROM borrower_embeddings "
            "ORDER BY embedding <-> %s::vector LIMIT %s",
            (vec_literal, k),
        )
        return [row[0] for row in cur.fetchall()]
