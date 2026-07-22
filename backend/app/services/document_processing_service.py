from app.services.chunking_service import create_chunks
from app.services.document_parser import extract_document_text
from app.services.embedding_service import generate_embeddings
from app.services.qdrant_service import upsert_chunks
from app.services.s3_service import download_document


def process_document(s3_key: str) -> dict:
    local_file = download_document(s3_key)

    try:
        pages = extract_document_text(local_file)
        chunks = create_chunks(pages)

        return {
            "s3_key": s3_key,
            "filename": local_file.name,
            "page_count": len(pages),
            "chunk_count": len(chunks),
            "chunks": chunks,
        }
    finally:
        if local_file.exists():
            local_file.unlink()


def index_document(s3_key: str) -> dict:
    result = process_document(s3_key)
    chunks = result["chunks"]

    if chunks:
        embeddings = generate_embeddings([chunk["text"] for chunk in chunks])
        indexed_count = upsert_chunks(
            s3_key=result["s3_key"],
            filename=result["filename"],
            chunks=chunks,
            embeddings=embeddings,
        )
    else:
        indexed_count = 0

    return {
        "s3_key": result["s3_key"],
        "filename": result["filename"],
        "page_count": result["page_count"],
        "chunk_count": result["chunk_count"],
        "indexed_count": indexed_count,
    }