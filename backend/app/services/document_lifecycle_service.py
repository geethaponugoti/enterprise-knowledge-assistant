from app.repositories.document_repository import (
    delete_document as delete_document_record,
)
from app.repositories.document_repository import get_document, upsert_document
from app.services.document_processing_service import index_document
from app.services.qdrant_service import delete_vectors_by_s3_key
from app.services.s3_service import (
    delete_s3_object,
    get_object_etag,
    list_supported_documents,
    upload_document,
)


def upload_and_index(filename: str, content: bytes, folder: str | None = None) -> dict:
    s3_key, etag = upload_document(filename, content, folder=folder)
    upsert_document(s3_key, filename, etag, status="indexing", chunk_count=0)

    try:
        result = index_document(s3_key)
    except (RuntimeError, ValueError):
        upsert_document(s3_key, filename, etag, status="failed", chunk_count=0)
        raise

    upsert_document(s3_key, filename, etag, status="indexed", chunk_count=result["chunk_count"])
    return result


def reindex_document(s3_key: str, filename: str) -> dict:
    etag = get_object_etag(s3_key)
    upsert_document(s3_key, filename, etag, status="indexing", chunk_count=0)

    try:
        result = index_document(s3_key)
    except (RuntimeError, ValueError):
        upsert_document(s3_key, filename, etag, status="failed", chunk_count=0)
        raise

    upsert_document(s3_key, filename, etag, status="indexed", chunk_count=result["chunk_count"])
    return result


def delete_document(s3_key: str, delete_source: bool = False) -> dict:
    delete_vectors_by_s3_key(s3_key)

    if delete_source:
        delete_s3_object(s3_key)

    delete_document_record(s3_key)

    return {
        "s3_key": s3_key,
        "vectors_deleted": True,
        "source_deleted": delete_source,
    }


def sync_from_s3() -> dict:
    s3_documents = list_supported_documents()
    indexed: list[str] = []
    skipped: list[str] = []
    failed: list[dict] = []

    for document in s3_documents:
        s3_key = document["key"]
        filename = document["filename"]
        etag = document["etag"]

        existing = get_document(s3_key)
        if existing and existing["etag"] == etag and existing["status"] == "indexed":
            skipped.append(s3_key)
            continue

        try:
            upsert_document(s3_key, filename, etag, status="indexing", chunk_count=0)
            result = index_document(s3_key)
            upsert_document(
                s3_key, filename, etag, status="indexed", chunk_count=result["chunk_count"]
            )
            indexed.append(s3_key)
        except (RuntimeError, ValueError) as exc:
            upsert_document(s3_key, filename, etag, status="failed", chunk_count=0)
            failed.append({"s3_key": s3_key, "error": str(exc)})

    return {
        "indexed": indexed,
        "skipped": skipped,
        "failed": failed,
        "total_s3_documents": len(s3_documents),
    }
