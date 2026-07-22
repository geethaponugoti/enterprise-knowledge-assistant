import uuid

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ApiException
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.config import get_settings

EMBEDDING_DIMENSIONS = 1536
POINT_ID_NAMESPACE = uuid.UUID("e42e40e9-829f-4ed0-b751-9f6f6057c48a")


def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    )


def qdrant_health() -> dict:
    client = get_qdrant_client()

    try:
        collections = client.get_collections().collections
    except ApiException as exc:
        raise RuntimeError(f"Unable to connect to Qdrant: {exc}") from exc

    return {
        "status": "connected",
        "collections": [collection.name for collection in collections],
    }


def ensure_collection_exists() -> None:
    settings = get_settings()
    client = get_qdrant_client()

    try:
        if client.collection_exists(settings.qdrant_collection):
            return

        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSIONS,
                distance=Distance.COSINE,
            ),
        )
    except ApiException as exc:
        raise RuntimeError(f"Unable to prepare Qdrant collection: {exc}") from exc


def build_point_id(s3_key: str, page: int, chunk_index: int) -> str:
    name = f"{s3_key}::{page}::{chunk_index}"
    return str(uuid.uuid5(POINT_ID_NAMESPACE, name))


def upsert_chunks(
    s3_key: str,
    filename: str,
    chunks: list[dict],
    embeddings: list[list[float]],
) -> int:
    settings = get_settings()
    client = get_qdrant_client()

    ensure_collection_exists()

    points = [
        PointStruct(
            id=build_point_id(s3_key, chunk["page"], chunk["chunk_index"]),
            vector=embedding,
            payload={
                "filename": filename,
                "s3_key": s3_key,
                "page": chunk["page"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "character_count": chunk["character_count"],
            },
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]

    try:
        client.upsert(collection_name=settings.qdrant_collection, points=points)
    except ApiException as exc:
        raise RuntimeError(f"Unable to store chunks in Qdrant: {exc}") from exc

    return len(points)


def search_similar_chunks(query_vector: list[float], top_k: int = 5) -> list[dict]:
    settings = get_settings()
    client = get_qdrant_client()

    try:
        results = client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        ).points
    except ApiException as exc:
        raise RuntimeError(f"Unable to search Qdrant: {exc}") from exc

    return [
        {
            "id": point.id,
            "score": point.score,
            "filename": point.payload.get("filename"),
            "s3_key": point.payload.get("s3_key"),
            "page": point.payload.get("page"),
            "chunk_index": point.payload.get("chunk_index"),
            "text": point.payload.get("text"),
        }
        for point in results
    ]


def get_chunks_by_s3_key(s3_key: str) -> list[dict]:
    settings = get_settings()
    client = get_qdrant_client()

    flt = Filter(must=[FieldCondition(key="s3_key", match=MatchValue(value=s3_key))])

    try:
        points, _ = client.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=flt,
            limit=500,
            with_payload=True,
        )
    except ApiException as exc:
        raise RuntimeError(f"Unable to fetch chunks for {s3_key}: {exc}") from exc

    chunks = [
        {
            "chunk_index": point.payload.get("chunk_index") or 0,
            "text": point.payload.get("text", ""),
        }
        for point in points
    ]
    chunks.sort(key=lambda chunk: chunk["chunk_index"])
    return chunks


def delete_vectors_by_s3_key(s3_key: str) -> None:
    settings = get_settings()
    client = get_qdrant_client()

    flt = Filter(must=[FieldCondition(key="s3_key", match=MatchValue(value=s3_key))])

    try:
        client.delete(collection_name=settings.qdrant_collection, points_selector=flt)
    except ApiException as exc:
        raise RuntimeError(f"Unable to delete vectors for {s3_key}: {exc}") from exc


def count_points() -> int:
    settings = get_settings()
    client = get_qdrant_client()

    try:
        if not client.collection_exists(settings.qdrant_collection):
            return 0
        return client.count(settings.qdrant_collection).count
    except ApiException as exc:
        raise RuntimeError(f"Unable to count Qdrant points: {exc}") from exc
