from app.services.chunking_service import create_chunks


def test_create_chunks_splits_long_text():
    long_text = "Sentence one. " * 200
    pages = [{"page": 1, "text": long_text}]

    chunks = create_chunks(pages, chunk_size=200, chunk_overlap=20)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk["page"] == 1
        assert chunk["character_count"] == len(chunk["text"])


def test_create_chunks_preserves_short_text_as_single_chunk():
    pages = [{"page": 1, "text": "Short text."}]

    chunks = create_chunks(pages, chunk_size=800, chunk_overlap=120)

    assert len(chunks) == 1
    assert chunks[0]["text"] == "Short text."
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["character_count"] == len("Short text.")


def test_create_chunks_indexes_sequentially_per_page():
    pages = [
        {"page": 1, "text": "A" * 500},
        {"page": 2, "text": "B" * 500},
    ]

    chunks = create_chunks(pages, chunk_size=200, chunk_overlap=0)

    page_1_chunks = [chunk for chunk in chunks if chunk["page"] == 1]
    page_2_chunks = [chunk for chunk in chunks if chunk["page"] == 2]

    assert [chunk["chunk_index"] for chunk in page_1_chunks] == list(range(len(page_1_chunks)))
    assert [chunk["chunk_index"] for chunk in page_2_chunks] == list(range(len(page_2_chunks)))
