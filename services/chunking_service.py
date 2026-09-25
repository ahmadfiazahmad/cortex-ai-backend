def split_into_chunks(
    text: str,
    chunk_token_size: int = 500,
    overlap_tokens: int = 50,
) -> list[dict]:
    words = text.split()

    if not words:
        return []

    if overlap_tokens >= chunk_token_size:
        raise ValueError("overlap_tokens must be smaller than chunk_token_size")

    chunks = []
    step = chunk_token_size - overlap_tokens

    for start in range(0, len(words), step):
        end = min(start + chunk_token_size, len(words))
        chunk_words = words[start:end]

        chunks.append(
            {
                "chunkIndex": len(chunks),
                "text": " ".join(chunk_words),
                "tokenCount": len(chunk_words),
            }
        )

        if end == len(words):
            break

    return chunks
