"""Thin clients for Ollama and Qdrant. Every connection problem becomes ServiceUnavailable,
so the API can tell the visitor exactly which service is down."""

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from rag.config import settings

DOCUMENT_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "


class ServiceUnavailable(Exception):
    """Raised when Ollama or Qdrant cannot be used. The message is safe to show visitors."""

    def __init__(self, service: str, message: str):
        self.service = service
        super().__init__(message)


def _ollama_down() -> ServiceUnavailable:
    return ServiceUnavailable(
        "ollama",
        f"Ollama is not reachable at {settings.ollama_url}. Start the Ollama app and try again.",
    )


def _ollama_post(path: str, payload: dict, timeout: float) -> dict:
    try:
        response = httpx.post(f"{settings.ollama_url}{path}", json=payload, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise ServiceUnavailable(
            "ollama", f"Ollama returned an error: {error.response.text[:200]}"
        ) from error
    except httpx.HTTPError as error:
        raise _ollama_down() from error
    return response.json()


def embed(texts: list[str], prefix: str) -> list[list[float]]:
    """Embed texts with nomic-embed-text, which expects a task prefix on every input."""
    data = _ollama_post(
        "/api/embed",
        {"model": settings.embed_model, "input": [prefix + text for text in texts]},
        timeout=120,
    )
    return data["embeddings"]


def chat(system: str, user: str) -> str:
    data = _ollama_post(
        "/api/chat",
        {
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": 0, "num_ctx": 4096},
        },
        timeout=180,
    )
    return data["message"]["content"].strip()


def qdrant() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url, timeout=5, check_compatibility=False)


def qdrant_down() -> ServiceUnavailable:
    return ServiceUnavailable(
        "qdrant",
        f"Qdrant is not reachable at {settings.qdrant_url}. "
        "Start it with: docker compose -f docker/compose.yml up -d",
    )


def collection_missing() -> ServiceUnavailable:
    return ServiceUnavailable(
        "qdrant",
        f"The Qdrant collection '{settings.collection}' is empty. Run: uv run python -m rag.ingest",
    )


def collection_size() -> int:
    """Number of stored chunks, 0 if the collection does not exist."""
    client = qdrant()
    try:
        if not client.collection_exists(settings.collection):
            return 0
        return client.count(settings.collection).count
    except (ResponseHandlingException, UnexpectedResponse, httpx.HTTPError) as error:
        raise qdrant_down() from error
