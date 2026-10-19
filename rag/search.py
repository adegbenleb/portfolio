"""Find the chunks most similar to a question."""

from dataclasses import dataclass

import httpx
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from rag.config import settings
from rag.services import QUERY_PREFIX, collection_missing, embed, qdrant, qdrant_down


@dataclass
class Hit:
    score: float
    payload: dict

    @property
    def text(self) -> str:
        return self.payload["text"]


def search(question: str, limit: int | None = None) -> list[Hit]:
    """Top chunks for a question, best first. Raises ServiceUnavailable if a service is down."""
    vector = embed([question], QUERY_PREFIX)[0]
    try:
        points = (
            qdrant()
            .query_points(
                settings.collection,
                query=vector,
                limit=limit or settings.top_k,
                with_payload=True,
            )
            .points
        )
    except UnexpectedResponse as error:
        if error.status_code == 404:
            raise collection_missing() from error
        raise qdrant_down() from error
    except (ResponseHandlingException, httpx.HTTPError) as error:
        raise qdrant_down() from error
    return [Hit(score=point.score, payload=point.payload) for point in points]
