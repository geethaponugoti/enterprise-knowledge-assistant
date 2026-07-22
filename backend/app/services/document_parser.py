from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


def extract_document_text(file_path: Path) -> list[dict]:
    extension = file_path.suffix.lower()

    if extension == ".txt":
        return extract_txt(file_path)

    if extension == ".pdf":
        return extract_pdf(file_path)

    if extension == ".docx":
        return extract_docx(file_path)

    raise ValueError(f"Unsupported document type: {extension}")


def extract_txt(file_path: Path) -> list[dict]:
    text = file_path.read_text(encoding="utf-8")

    return [
        {
            "page": 1,
            "text": text,
        }
    ]


def extract_pdf(file_path: Path) -> list[dict]:
    reader = PdfReader(str(file_path))
    pages: list[dict] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        if text.strip():
            pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )

    return pages


def extract_docx(file_path: Path) -> list[dict]:
    document = DocxDocument(str(file_path))

    text = "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    )

    return [
        {
            "page": 1,
            "text": text,
        }
    ]