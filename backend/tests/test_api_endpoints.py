from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@patch("app.main.qdrant_health")
def test_health_check_qdrant(mock_qdrant_health):
    mock_qdrant_health.return_value = {
        "status": "connected",
        "collections": ["enterprise_documents"],
    }

    response = client.get("/health/qdrant")

    assert response.status_code == 200
    assert response.json()["status"] == "connected"


@patch("app.api.documents.list_supported_documents")
def test_get_s3_documents(mock_list_documents):
    mock_list_documents.return_value = [
        {
            "key": "Documents/hr/leave_policy.txt",
            "filename": "leave_policy.txt",
            "size_bytes": 100,
            "etag": "abc",
            "last_modified": "2026-01-01",
        }
    ]

    response = client.get("/documents/s3")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["documents"][0]["filename"] == "leave_policy.txt"


@patch("app.api.documents.list_supported_documents")
def test_get_s3_documents_wraps_errors_as_500(mock_list_documents):
    mock_list_documents.side_effect = RuntimeError("S3 is down")

    response = client.get("/documents/s3")

    assert response.status_code == 500
    assert "S3 is down" in response.json()["detail"]


@patch("app.api.assistant.answer_question")
def test_ask_question(mock_answer_question):
    mock_answer_question.return_value = {
        "answer": "15 vacation days.",
        "grounded": True,
        "sources": [],
        "retrieval_latency_ms": 10.0,
        "generation_latency_ms": 20.0,
    }

    response = client.post("/assistant/ask", json={"question": "How many vacation days?"})

    assert response.status_code == 200
    assert response.json()["grounded"] is True


def test_ask_question_rejects_empty_question():
    response = client.post("/assistant/ask", json={"question": ""})

    assert response.status_code == 422


@patch("app.api.documents.upload_and_index")
def test_upload_document_rejects_unsupported_extension(mock_upload_and_index):
    response = client.post(
        "/documents/upload",
        files={"file": ("sample.csv", b"a,b,c", "text/csv")},
    )

    assert response.status_code == 400
    mock_upload_and_index.assert_not_called()
