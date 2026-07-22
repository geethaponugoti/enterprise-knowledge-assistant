from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.repositories.document_repository import list_documents
from app.services.document_lifecycle_service import (
    delete_document,
    reindex_document,
    sync_from_s3,
    upload_and_index,
)
from app.services.document_processing_service import index_document, process_document
from app.services.s3_service import SUPPORTED_EXTENSIONS, list_supported_documents

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/s3")
def get_s3_documents() -> dict:
    try:
        documents = list_supported_documents()
        return {"count": len(documents), "documents": documents}
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/preview")
def preview_document(s3_key: str) -> dict:
    try:
        result = process_document(s3_key)
        result["chunks"] = result["chunks"][:5]
        return result

    except (RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

@router.post("/index")
def index_document_endpoint(s3_key: str) -> dict:
    try:
        return index_document(s3_key)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post("/upload")
async def upload_document_endpoint(
    file: UploadFile = File(...),
    folder: str | None = Form(default=None),
) -> dict:
    extension = Path(file.filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: {extension}. "
                f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
            ),
        )

    content = await file.read()

    try:
        return upload_and_index(file.filename, content, folder=folder)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sync")
def sync_documents_endpoint() -> dict:
    try:
        return sync_from_s3()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/reindex")
def reindex_document_endpoint(s3_key: str, filename: str) -> dict:
    try:
        return reindex_document(s3_key, filename)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/vectors")
def delete_document_endpoint(s3_key: str, delete_source: bool = False) -> dict:
    try:
        return delete_document(s3_key, delete_source=delete_source)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/indexed")
def list_indexed_documents_endpoint() -> dict:
    documents = list_documents()
    return {"count": len(documents), "documents": documents}
