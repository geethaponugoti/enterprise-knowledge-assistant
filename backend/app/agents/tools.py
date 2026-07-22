from langchain_core.tools import tool

from app.config import get_settings
from app.repositories.document_repository import count_documents, list_documents
from app.services.embedding_service import generate_embedding, get_openai_client
from app.services.qdrant_service import (
    count_points,
    get_chunks_by_s3_key,
    search_similar_chunks,
)
from app.services.rag_service import answer_question
from app.services.s3_service import list_supported_documents


def _resolve_s3_key(filename: str) -> str | None:
    documents = list_documents()
    filename_lower = filename.lower()

    for document in documents:
        if document["filename"].lower() == filename_lower:
            return document["s3_key"]

    for document in documents:
        if filename_lower in document["filename"].lower():
            return document["s3_key"]

    return None


@tool
def search_documents(query: str, top_k: int = 5) -> list[dict]:
    """Semantically search across all indexed enterprise documents for the
    given query. Returns matching chunks with filename, page, an excerpt,
    and a relevance score."""
    query_vector = generate_embedding(query)
    matches = search_similar_chunks(query_vector, top_k=top_k)
    return [
        {
            "filename": match["filename"],
            "page": match["page"],
            "excerpt": match["text"][:250],
            "score": round(match["score"], 4),
        }
        for match in matches
    ]


@tool
def search_by_department(query: str, department: str) -> list[dict]:
    """Search documents scoped to a specific department folder, such as hr,
    it, finance, or operations. Returns matching chunks with filename, page,
    an excerpt, and a relevance score."""
    query_vector = generate_embedding(query)
    matches = search_similar_chunks(query_vector, top_k=20)
    filtered = [
        match for match in matches if department.lower() in match["s3_key"].lower()
    ]
    return [
        {
            "filename": match["filename"],
            "page": match["page"],
            "excerpt": match["text"][:250],
            "score": round(match["score"], 4),
        }
        for match in filtered[:5]
    ]


@tool
def list_s3_documents() -> list[dict]:
    """List all supported documents currently stored in the S3 knowledge
    repository, with filename and size."""
    documents = list_supported_documents()
    return [
        {
            "filename": document["filename"],
            "s3_key": document["key"],
            "size_bytes": document["size_bytes"],
        }
        for document in documents
    ]


@tool
def list_indexed_documents() -> list[dict]:
    """List all documents that have been indexed into the vector database,
    with their indexing status and chunk count."""
    documents = list_documents()
    return [
        {
            "filename": document["filename"],
            "status": document["status"],
            "chunk_count": document["chunk_count"],
            "indexed_at": document["indexed_at"],
        }
        for document in documents
    ]


@tool
def inspect_document_metadata(filename: str) -> dict:
    """Look up indexing metadata for a specific document by filename,
    including status, chunk count, and when it was last indexed."""
    documents = list_documents()
    filename_lower = filename.lower()

    for document in documents:
        if filename_lower in document["filename"].lower():
            return document

    return {"error": f"No indexed document found matching '{filename}'."}


@tool
def summarize_document(filename: str) -> str:
    """Generate a concise summary of a specific document by filename. Use
    this when asked to summarize a document."""
    s3_key = _resolve_s3_key(filename)
    if not s3_key:
        return f"No indexed document found matching '{filename}'."

    chunks = get_chunks_by_s3_key(s3_key)
    if not chunks:
        return f"No indexed content found for '{filename}'."

    full_text = "\n\n".join(chunk["text"] for chunk in chunks)
    settings = get_settings()
    client = get_openai_client()

    response = client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {
                "role": "system",
                "content": "Summarize the following enterprise document concisely, in 3-5 sentences.",
            },
            {"role": "user", "content": full_text[:12000]},
        ],
    )
    return response.choices[0].message.content


@tool
def compare_documents(filename_a: str, filename_b: str) -> str:
    """Compare two documents by filename and explain their key differences.
    Use this for questions asking to compare, diff, or contrast two
    documents."""
    s3_key_a = _resolve_s3_key(filename_a)
    s3_key_b = _resolve_s3_key(filename_b)

    if not s3_key_a:
        return f"No indexed document found matching '{filename_a}'."
    if not s3_key_b:
        return f"No indexed document found matching '{filename_b}'."

    text_a = "\n\n".join(chunk["text"] for chunk in get_chunks_by_s3_key(s3_key_a))
    text_b = "\n\n".join(chunk["text"] for chunk in get_chunks_by_s3_key(s3_key_b))

    settings = get_settings()
    client = get_openai_client()

    response = client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {
                "role": "system",
                "content": "Compare the two enterprise documents below and summarize their key differences.",
            },
            {
                "role": "user",
                "content": (
                    f"Document A ({filename_a}):\n{text_a[:6000]}\n\n"
                    f"Document B ({filename_b}):\n{text_b[:6000]}"
                ),
            },
        ],
    )
    return response.choices[0].message.content


@tool
def document_statistics() -> dict:
    """Return overall statistics about the knowledge base: number of S3
    documents, number of indexed documents, and number of vector chunks
    stored in Qdrant."""
    return {
        "s3_document_count": len(list_supported_documents()),
        "indexed_document_count": count_documents(status="indexed"),
        "qdrant_point_count": count_points(),
    }


@tool
def answer_from_documents(question: str) -> dict:
    """Answer a specific factual question using the standard grounded RAG
    pipeline. Use this for direct question-answering sub-tasks within a
    larger multi-step request."""
    result = answer_question(question)
    return {
        "answer": result["answer"],
        "grounded": result["grounded"],
        "sources": [source["filename"] for source in result["sources"]],
    }


ALL_TOOLS = [
    search_documents,
    search_by_department,
    list_s3_documents,
    list_indexed_documents,
    inspect_document_metadata,
    summarize_document,
    compare_documents,
    document_statistics,
    answer_from_documents,
]
