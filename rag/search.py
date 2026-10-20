"""Find the chunks that answer a question.

Two kinds of retrieval are merged:
1. Semantic: the top k chunks by similarity to the question.
2. Entity: if the question names a company or project from content/ (for example "Miele" or
   "ShopFlow"), every chunk for it is added too. A broad question like "What did he do at
   Miele?" otherwise returns only the 5 most similar Miele bullets and misses the rest.
"""

import re
from dataclasses import dataclass

import httpx
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from qdrant_client.models import FieldCondition, Filter, MatchValue

from api import content
from rag.config import settings
from rag.services import QUERY_PREFIX, collection_missing, embed, qdrant, qdrant_down

MAX_ENTITY_CHUNKS = 50


@dataclass
class Hit:
    score: float
    payload: dict
    id: str = ""

    @property
    def text(self) -> str:
        return self.payload["text"]


def entities() -> dict[str, str]:
    """Names a visitor might type, mapped to the chunk label they belong to.

    Read from content/ on every call, so a new role or project works after re-ingesting.
    """
    names = {role["company"]: role["company"] for role in content.load_experience()}
    for project in content.load_projects():
        # "ShopFlow: E-commerce Analytics Platform" can be asked about as "ShopFlow".
        names[project["title"].split(":")[0].strip()] = project["title"]
        names[project["title"]] = project["title"]
    return names


def named_labels(question: str) -> list[str]:
    """Chunk labels for every company or project named in the question."""
    labels = []
    for name, label in entities().items():
        if re.search(rf"\b{re.escape(name)}\b", question, re.IGNORECASE) and label not in labels:
            labels.append(label)
    return labels


def search(question: str, limit: int | None = None) -> list[Hit]:
    """Chunks for a question, best score first. Raises ServiceUnavailable if a service is down."""
    vector = embed([question], QUERY_PREFIX)[0]
    client = qdrant()
    try:
        points = client.query_points(
            settings.collection, query=vector, limit=limit or settings.top_k, with_payload=True
        ).points
        for label in named_labels(question):
            points += client.query_points(
                settings.collection,
                query=vector,
                query_filter=Filter(
                    must=[FieldCondition(key="label", match=MatchValue(value=label))]
                ),
                limit=MAX_ENTITY_CHUNKS,
                with_payload=True,
            ).points
    except UnexpectedResponse as error:
        if error.status_code == 404:
            raise collection_missing() from error
        raise qdrant_down() from error
    except (ResponseHandlingException, httpx.HTTPError) as error:
        raise qdrant_down() from error

    unique = {str(point.id): point for point in points}
    hits = [Hit(score=p.score, payload=p.payload, id=pid) for pid, p in unique.items()]
    return sorted(hits, key=lambda hit: hit.score, reverse=True)
