from datetime import datetime, timezone

from app.db import get_connection


def log_query(
    question: str,
    grounded: bool,
    source_count: int,
    retrieval_latency_ms: float,
    generation_latency_ms: float,
    error: str | None = None,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO query_logs
                (question, grounded, source_count, retrieval_latency_ms,
                 generation_latency_ms, error, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                question,
                int(grounded),
                source_count,
                retrieval_latency_ms,
                generation_latency_ms,
                error,
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def get_query_stats() -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_questions,
                AVG(retrieval_latency_ms) AS avg_retrieval_latency_ms,
                AVG(generation_latency_ms) AS avg_generation_latency_ms
            FROM query_logs
            WHERE error IS NULL
            """
        ).fetchone()
        return dict(row)


def get_recent_errors(limit: int = 10) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT question, error, created_at FROM query_logs
            WHERE error IS NOT NULL
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
