import json
import time

from openai import OpenAIError

from app.config import get_settings
from app.repositories.query_log_repository import log_query
from app.services.embedding_service import generate_embedding, get_openai_client
from app.services.qdrant_service import search_similar_chunks

SYSTEM_PROMPT = (
    "You are an enterprise knowledge assistant. You will be given a numbered "
    "list of context chunks and a question. Answer the question using only "
    "the provided context, citing source filenames inline. Respond with a "
    "JSON object with three fields: \"answer\" (plain text answer), "
    "\"grounded\" (true only if the context actually contained enough "
    "information to answer the question), and \"used_chunks\" (a list of "
    "the integer chunk numbers you actually relied on to answer — empty "
    "if grounded is false)."
)


def answer_question(
    question: str,
    top_k: int | None = None,
    score_threshold: float | None = None,
) -> dict:
    settings = get_settings()
    top_k = settings.rag_top_k if top_k is None else top_k
    score_threshold = (
        settings.rag_score_threshold if score_threshold is None else score_threshold
    )

    retrieval_latency_ms = 0.0
    generation_latency_ms = 0.0

    try:
        retrieval_started = time.perf_counter()
        query_vector = generate_embedding(question)
        matches = search_similar_chunks(query_vector, top_k=top_k)
        matches = [match for match in matches if match["score"] >= score_threshold]
        retrieval_latency_ms = (time.perf_counter() - retrieval_started) * 1000

        if not matches:
            log_query(question, False, 0, retrieval_latency_ms, 0.0)
            return {
                "answer": "I don't have any indexed documents relevant to this question.",
                "grounded": False,
                "sources": [],
                "retrieval_latency_ms": round(retrieval_latency_ms, 1),
                "generation_latency_ms": 0.0,
            }

        context = _build_context(matches)
        client = get_openai_client()

        generation_started = time.perf_counter()
        response = client.chat.completions.create(
            model=settings.chat_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}",
                },
            ],
        )
        generation_latency_ms = (time.perf_counter() - generation_started) * 1000

    except OpenAIError as exc:
        log_query(
            question, False, 0, retrieval_latency_ms, generation_latency_ms, error=str(exc)
        )
        raise RuntimeError(f"Unable to generate answer: {exc}") from exc
    except RuntimeError as exc:
        log_query(
            question, False, 0, retrieval_latency_ms, generation_latency_ms, error=str(exc)
        )
        raise

    parsed = json.loads(response.choices[0].message.content)
    grounded = parsed.get("grounded", False)
    sources = _select_sources(matches, parsed.get("used_chunks", []), grounded)

    log_query(question, grounded, len(sources), retrieval_latency_ms, generation_latency_ms)

    return {
        "answer": parsed.get("answer", ""),
        "grounded": grounded,
        "sources": sources,
        "retrieval_latency_ms": round(retrieval_latency_ms, 1),
        "generation_latency_ms": round(generation_latency_ms, 1),
    }


def _build_context(matches: list[dict]) -> str:
    return "\n\n".join(
        f"[Chunk {index}] (Source: {match['filename']})\n{match['text']}"
        for index, match in enumerate(matches, start=1)
    )


def _select_sources(matches: list[dict], used_chunks: list[int], grounded: bool) -> list[dict]:
    if not grounded:
        return []

    used = set(used_chunks or [])
    selected = (
        matches
        if not used
        else [match for index, match in enumerate(matches, start=1) if index in used]
    )

    return [
        {
            "chunk_id": match["id"],
            "filename": match["filename"],
            "s3_key": match["s3_key"],
            "page": match["page"],
            "chunk_index": match["chunk_index"],
            "excerpt": match["text"][:300],
            "score": round(match["score"], 4),
        }
        for match in selected
    ]
