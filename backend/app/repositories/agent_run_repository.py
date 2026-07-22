import json
from datetime import datetime, timezone

from app.db import get_connection


def log_agent_run(
    thread_id: str,
    question: str,
    status: str,
    tools_used: list[str],
    trace: list[dict],
    step_count: int,
    latency_ms: float,
    error: str | None = None,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO agent_runs
                (thread_id, question, status, tools_used, trace, step_count,
                 latency_ms, error, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                thread_id,
                question,
                status,
                json.dumps(tools_used),
                json.dumps(trace),
                step_count,
                latency_ms,
                error,
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def get_agent_stats() -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_runs,
                AVG(latency_ms) AS avg_latency_ms
            FROM agent_runs
            WHERE error IS NULL
            """
        ).fetchone()
        return dict(row)


def get_recent_runs(limit: int = 10) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT thread_id, question, status, tools_used, trace, step_count,
                   latency_ms, error, created_at
            FROM agent_runs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        results = []
        for row in rows:
            item = dict(row)
            item["tools_used"] = json.loads(item["tools_used"]) if item["tools_used"] else []
            item["trace"] = json.loads(item["trace"]) if item["trace"] else []
            results.append(item)
        return results
