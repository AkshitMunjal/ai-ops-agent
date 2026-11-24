import os

import httpx
from dotenv import load_dotenv

from cost_control.limit import check_spend_limit
from cost_control.recorder import record_usage
from rag.settings import EMBEDDING_SIZE, get_embedding_model

load_dotenv()

embeddings_url = "https://openrouter.ai/api/v1/embeddings"

# How many texts are sent to the embedding service in one request.
BATCH_SIZE = 50


class EmbeddingError(Exception):
    """The embedding service failed or gave an unexpected answer."""


def embed_batch(texts):
    # Stops with SpendLimitReached if the daily limit is used up.
    check_spend_limit()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    model_name = get_embedding_model()

    headers = {"Authorization": f"Bearer {api_key}"}
    body = {"model": model_name, "input": texts}

    try:
        response = httpx.post(embeddings_url, headers=headers, json=body, timeout=60)
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise EmbeddingError(f"The embedding service failed: {error}") from error

    data = response.json()

    usage = data.get("usage") or {}
    try:
        record_usage(model_name, usage)
    except Exception as error:
        print(f"Could not save the embedding usage: {error}")

    if "data" not in data:
        raise EmbeddingError("The embedding service answered without any data.")

    items = sorted(data["data"], key=lambda item: item.get("index", 0))
    vectors = [item["embedding"] for item in items]

    if len(vectors) != len(texts):
        raise EmbeddingError("The embedding service returned the wrong number of vectors.")

    for vector in vectors:
        if len(vector) != EMBEDDING_SIZE:
            raise EmbeddingError(
                f"Expected {EMBEDDING_SIZE} numbers per text but got {len(vector)}. "
                "Check EMBEDDING_MODEL in .env."
            )

    return vectors


def embed_texts(texts):
    vectors = []

    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start:start + BATCH_SIZE]
        vectors.extend(embed_batch(batch))

    return vectors
