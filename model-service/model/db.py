"""
Postgres/pgvector connectivity for cohort similarity search.

Optional in every sense: connect() returns None instead of raising if
Postgres isn't reachable, and every function here is written so its
caller (scoring.py) can catch a failure and fall back to the in-process
scikit-learn NearestNeighbors lookup that was already there. A missing or
unreachable database should degrade the *adaptivity* of the cold-start
estimate, never break scoring outright.
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
    except Exception as e:
        # TEMPORARY diagnostic -- remove once pgvector is confirmed working.
        print(f"[DEBUG db] Postgres connect() failed: {type(e).__name__}: {e}", flush=True)
        return None


def _to_vector_literal(vec) -> str:
    # pgvector's text input format: '[0.1,0.2,...]'. Passed as a plain
    # string parameter with an explicit ::vector cast in the SQL below,
    # rather than relying on implicit type inference.
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
