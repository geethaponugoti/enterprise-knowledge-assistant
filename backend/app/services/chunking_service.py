from langchain_text_splitters import RecursiveCharacterTextSplitter


def create_chunks(
    pages: list[dict],
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[dict] = []

    for page in pages:
        page_chunks = splitter.split_text(page["text"])

        for chunk_index, chunk_text in enumerate(page_chunks):
            chunks.append(
                {
                    "page": page["page"],
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "character_count": len(chunk_text),
                }
            )

    return chunks