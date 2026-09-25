import os

import requests
from dotenv import load_dotenv

from utils.retry import with_retry

load_dotenv()

OPENAI_API_URL = "https://api.openai.com/v1/embeddings"
OPENAI_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
MAX_RETRIES = int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))
BASE_DELAY_SECONDS = float(os.getenv("EMBEDDING_RETRY_BASE_DELAY_MS", "500")) / 1000


def _embed_batch(texts: list[str]) -> list[list[float]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    response = requests.post(
        OPENAI_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENAI_MODEL,
            "input": texts,
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Embedding API returned {response.status_code}: {response.text[:500]}"
        )

    data = response.json().get("data", [])
    data.sort(key=lambda item: item["index"])
    embeddings = [item["embedding"] for item in data]

    if len(embeddings) != len(texts):
        raise RuntimeError("Embedding API returned an unexpected number of embeddings.")

    return embeddings


def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    return with_retry(
        lambda: _embed_batch(texts),
        max_retries=MAX_RETRIES,
        base_delay_seconds=BASE_DELAY_SECONDS,
    )


def embed_query(text: str) -> list[float]:
    return embed_batch([text])[0]
