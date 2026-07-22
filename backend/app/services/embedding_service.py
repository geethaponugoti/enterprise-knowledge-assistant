from openai import OpenAI, OpenAIError

from app.config import get_settings


def get_openai_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key)


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    client = get_openai_client()

    try:
        response = client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
        )
    except OpenAIError as exc:
        raise RuntimeError(f"Unable to generate embeddings: {exc}") from exc

    return [item.embedding for item in response.data]


def generate_embedding(text: str) -> list[float]:
    return generate_embeddings([text])[0]
