import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                s3_key TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                etag TEXT NOT NULL,
                status TEXT NOT NULL,
                chunk_count INTEGER NOT NULL DEFAULT 0,
                indexed_at TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                grounded INTEGER NOT NULL,
                source_count INTEGER NOT NULL,
                retrieval_latency_ms REAL NOT NULL,
                generation_latency_ms REAL NOT NULL,
                error TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                question TEXT NOT NULL,
                status TEXT NOT NULL,
                tools_used TEXT,
                trace TEXT,
                step_count INTEGER NOT NULL DEFAULT 0,
                latency_ms REAL NOT NULL,
                error TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
