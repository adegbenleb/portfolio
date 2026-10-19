"""Rebuild the Qdrant collection from content/. Run with: uv run python -m rag.ingest

The collection is recreated on every run and chunk IDs are deterministic, so running it twice
gives exactly the same index. Re-run it after every change in content/.
"""

import sys
from collections import Counter

import httpx
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from qdrant_client.models import Distance, PointStruct, VectorParams

from rag.chunks import build_chunks
from rag.config import settings
from rag.services import DOCUMENT_PREFIX, ServiceUnavailable, embed, qdrant, qdrant_down


def ingest() -> Counter:
    chunks = build_chunks()
    vectors = embed([chunk.text for chunk in chunks], DOCUMENT_PREFIX)

    client = qdrant()
    try:
        if client.collection_exists(settings.collection):
            client.delete_collection(settings.collection)
        client.create_collection(
            settings.collection,
            vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
        )
        client.upsert(
            settings.collection,
            points=[
                PointStruct(id=chunk.id, vector=vector, payload=chunk.payload)
                for chunk, vector in zip(chunks, vectors, strict=True)
            ],
            wait=True,
        )
    except (ResponseHandlingException, UnexpectedResponse, httpx.HTTPError) as error:
        raise qdrant_down() from error
    return Counter(chunk.file for chunk in chunks)


def main() -> None:
    try:
        counts = ingest()
    except ServiceUnavailable as error:
        sys.exit(str(error))
    width = max(len(file) for file in counts)
    for file, count in sorted(counts.items()):
        print(f"{file:<{width}}  {count:>3} chunks")
    print(f"{'total':<{width}}  {sum(counts.values()):>3} chunks in '{settings.collection}'")


if __name__ == "__main__":
    main()
