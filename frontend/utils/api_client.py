import os
from typing import Any

import requests

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:8000",
)


class APIClientError(RuntimeError):
    """Raised when the frontend cannot communicate with the backend."""


def get_health() -> dict[str, Any]:
    return _get("/health")


def get_qdrant_health() -> dict[str, Any]:
    return _get("/health/qdrant")


def get_s3_documents() -> dict[str, Any]:
    return _get("/documents/s3", timeout=30)


def get_indexed_documents() -> dict[str, Any]:
    return _get("/documents/indexed", timeout=30)


def upload_document(
    filename: str,
    content: bytes,
    folder: str | None = None,
) -> dict[str, Any]:
    try:
        response = requests.post(
            f"{BACKEND_URL}/documents/upload",
            files={"file": (filename, content)},
            data={"folder": folder} if folder else None,
            timeout=120,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise APIClientError(f"Unable to upload {filename}: {exc}") from exc


def sync_documents() -> dict[str, Any]:
    return _post("/documents/sync", timeout=120)


def reindex_document(s3_key: str, filename: str) -> dict[str, Any]:
    return _post(
        "/documents/reindex",
        params={"s3_key": s3_key, "filename": filename},
        timeout=60,
    )


def delete_document(s3_key: str, delete_source: bool = False) -> dict[str, Any]:
    return _delete(
        "/documents/vectors",
        params={"s3_key": s3_key, "delete_source": delete_source},
        timeout=30,
    )


def run_agent(question: str, thread_id: str) -> dict[str, Any]:
    return _post_json(
        "/agent/run",
        {"question": question, "thread_id": thread_id},
        timeout=120,
    )


def get_monitoring_stats() -> dict[str, Any]:
    return _get("/monitoring/stats", timeout=30)


def ask_assistant(
    question: str,
    top_k: int | None = None,
    score_threshold: float | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"question": question}
    if top_k is not None:
        payload["top_k"] = top_k
    if score_threshold is not None:
        payload["score_threshold"] = score_threshold

    return _post_json("/assistant/ask", payload, timeout=60)


def _get(
    endpoint: str,
    timeout: int = 10,
) -> dict[str, Any]:
    try:
        response = requests.get(
            f"{BACKEND_URL}{endpoint}",
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        raise APIClientError(
            f"Unable to reach {endpoint}: {exc}"
        ) from exc


def _post(
    endpoint: str,
    params: dict[str, Any] | None = None,
    timeout: int = 10,
) -> dict[str, Any]:
    try:
        response = requests.post(
            f"{BACKEND_URL}{endpoint}",
            params=params,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        raise APIClientError(
            f"Unable to reach {endpoint}: {exc}"
        ) from exc


def _delete(
    endpoint: str,
    params: dict[str, Any] | None = None,
    timeout: int = 10,
) -> dict[str, Any]:
    try:
        response = requests.delete(
            f"{BACKEND_URL}{endpoint}",
            params=params,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        raise APIClientError(
            f"Unable to reach {endpoint}: {exc}"
        ) from exc


def _post_json(
    endpoint: str,
    payload: dict[str, Any],
    timeout: int = 10,
) -> dict[str, Any]:
    try:
        response = requests.post(
            f"{BACKEND_URL}{endpoint}",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        raise APIClientError(
            f"Unable to reach {endpoint}: {exc}"
        ) from exc