from fastapi import APIRouter

from app.repositories.agent_run_repository import get_agent_stats, get_recent_runs
from app.repositories.document_repository import count_documents
from app.repositories.query_log_repository import get_query_stats, get_recent_errors
from app.services.qdrant_service import count_points
from app.services.s3_service import list_supported_documents

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/stats")
def get_stats() -> dict:
    try:
        s3_document_count = len(list_supported_documents())
    except RuntimeError:
        s3_document_count = None

    try:
        qdrant_point_count = count_points()
    except RuntimeError:
        qdrant_point_count = None

    query_stats = get_query_stats()
    agent_stats = get_agent_stats()

    return {
        "s3_document_count": s3_document_count,
        "indexed_document_count": count_documents(status="indexed"),
        "qdrant_point_count": qdrant_point_count,
        "questions_asked": query_stats["total_questions"] or 0,
        "avg_retrieval_latency_ms": round(query_stats["avg_retrieval_latency_ms"] or 0, 1),
        "avg_generation_latency_ms": round(query_stats["avg_generation_latency_ms"] or 0, 1),
        "agent_runs": agent_stats["total_runs"] or 0,
        "avg_agent_latency_ms": round(agent_stats["avg_latency_ms"] or 0, 1),
        "recent_errors": get_recent_errors(limit=10),
        "recent_agent_runs": get_recent_runs(limit=10),
    }
