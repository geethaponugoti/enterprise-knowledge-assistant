from datetime import datetime, timezone

from app.db import get_connection


def upsert_document(
    s3_key: str,
    filename: str,
    etag: str,
    status: str,
    chunk_count: int,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    indexed_at = now if status == "indexed" else None

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (s3_key, filename, etag, status, chunk_count, indexed_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(s3_key) DO UPDATE SET
                filename = excluded.filename,
                etag = excluded.etag,
                status = excluded.status,
                chunk_count = excluded.chunk_count,
                indexed_at = COALESCE(excluded.indexed_at, documents.indexed_at),
                updated_at = excluded.updated_at
            """,
            (s3_key, filename, etag, status, chunk_count, indexed_at, now),
        )


def get_document(s3_key: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM documents WHERE s3_key = ?", (s3_key,)
        ).fetchone()
        return dict(row) if row else None


def list_documents() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM documents ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def delete_document(s3_key: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM documents WHERE s3_key = ?", (s3_key,))


def count_documents(status: str | None = None) -> int:
    with get_connection() as connection:
        if status:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM documents WHERE status = ?",
                (status,),
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM documents"
            ).fetchone()
        return row["count"]
