import json
from unittest.mock import MagicMock, patch

from app.services.rag_service import answer_question


def _make_matches():
    return [
        {
            "id": "id-1",
            "score": 0.6,
            "filename": "leave_policy.txt",
            "s3_key": "Documents/hr/leave_policy.txt",
            "page": 1,
            "chunk_index": 0,
            "text": "Employees receive 15 vacation days per year.",
        },
        {
            "id": "id-2",
            "score": 0.1,
            "filename": "unrelated.txt",
            "s3_key": "Documents/it/unrelated.txt",
            "page": 1,
            "chunk_index": 0,
            "text": "Unrelated low-score content.",
        },
    ]


def _mock_openai_response(payload: dict):
    message = MagicMock()
    message.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


@patch("app.services.rag_service.log_query")
@patch("app.services.rag_service.get_openai_client")
@patch("app.services.rag_service.search_similar_chunks")
@patch("app.services.rag_service.generate_embedding")
def test_low_score_matches_are_filtered_by_threshold(
    mock_generate_embedding, mock_search, mock_get_client, mock_log_query
):
    mock_generate_embedding.return_value = [0.1] * 1536
    mock_search.return_value = _make_matches()

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_response(
        {"answer": "Employees get 15 vacation days.", "grounded": True, "used_chunks": [1]}
    )
    mock_get_client.return_value = mock_client

    result = answer_question("How many vacation days?", top_k=5, score_threshold=0.3)

    context_message = mock_client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
    assert "unrelated.txt" not in context_message
    assert "leave_policy.txt" in context_message
    assert result["grounded"] is True
    assert len(result["sources"]) == 1
    assert result["sources"][0]["filename"] == "leave_policy.txt"


@patch("app.services.rag_service.log_query")
@patch("app.services.rag_service.get_openai_client")
@patch("app.services.rag_service.search_similar_chunks")
@patch("app.services.rag_service.generate_embedding")
def test_ungrounded_answer_has_no_sources(
    mock_generate_embedding, mock_search, mock_get_client, mock_log_query
):
    mock_generate_embedding.return_value = [0.1] * 1536
    mock_search.return_value = [_make_matches()[0]]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_response(
        {"answer": "I don't have enough information.", "grounded": False, "used_chunks": []}
    )
    mock_get_client.return_value = mock_client

    result = answer_question("What is the CEO's name?", top_k=5, score_threshold=0.0)

    assert result["grounded"] is False
    assert result["sources"] == []


@patch("app.services.rag_service.log_query")
@patch("app.services.rag_service.search_similar_chunks")
@patch("app.services.rag_service.generate_embedding")
def test_no_matches_returns_ungrounded_without_calling_openai(
    mock_generate_embedding, mock_search, mock_log_query
):
    mock_generate_embedding.return_value = [0.1] * 1536
    mock_search.return_value = []

    result = answer_question("Anything?", top_k=5, score_threshold=0.2)

    assert result["grounded"] is False
    assert result["sources"] == []
    assert "don't have any indexed documents" in result["answer"]
