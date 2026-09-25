import os
from pathlib import Path
from uuid import UUID

from config.database import connect_to_database
from services.chunking_service import split_into_chunks
from services.embedding_service import embed_batch
from services.extraction_service import extract_text

CHUNK_TOKEN_SIZE = int(os.getenv("CHUNK_TOKEN_SIZE", "500"))
CHUNK_TOKEN_OVERLAP = int(os.getenv("CHUNK_TOKEN_OVERLAP", "50"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "20"))


def _update_document_status(document_id, status, page_count=None, error_message=None):
    with connect_to_database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE documents
                SET status = %s,
                    page_count = COALESCE(%s, page_count),
                    error_message = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (status, page_count, error_message, document_id),
            )


def _insert_chunks(document_id, chunks):
    if not chunks:
        return []

    rows = []
    with connect_to_database() as connection:
        with connection.cursor() as cursor:
            for chunk in chunks:
                chunk_id = __import__("uuid").uuid4()
                cursor.execute(
                    """
                    INSERT INTO chunks (
                        id, document_id, chunk_index, text, token_count
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, text
                    """,
                    (
                        chunk_id,
                        document_id,
                        chunk["chunkIndex"],
                        chunk["text"],
                        chunk["tokenCount"],
                    ),
                )
                row = cursor.fetchone()
                rows.append({"id": row[0], "text": row[1]})

    return rows


def _mark_chunk_ready(chunk_id, embedding):
    vector_literal = "[" + ",".join(str(value) for value in embedding) + "]"
    with connect_to_database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE chunks
                SET embedding = %s::vector,
                    embedding_status = 'ready'
                WHERE id = %s
                """,
                (vector_literal, chunk_id),
            )


def _mark_chunk_failed(chunk_id):
    with connect_to_database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE chunks
                SET embedding_status = 'failed',
                    embedding_attempts = embedding_attempts + 1
                WHERE id = %s
                """,
                (chunk_id,),
            )


def _count_not_ready(document_id):
    with connect_to_database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM chunks
                WHERE document_id = %s AND embedding_status != 'ready'
                """,
                (document_id,),
            )
            return cursor.fetchone()[0]


def embed_chunks(chunk_rows):
    for start in range(0, len(chunk_rows), EMBEDDING_BATCH_SIZE):
        batch = chunk_rows[start : start + EMBEDDING_BATCH_SIZE]
        texts = [row["text"] for row in batch]

        try:
            embeddings = embed_batch(texts)
            for row, embedding in zip(batch, embeddings):
                _mark_chunk_ready(row["id"], embedding)
        except Exception as exc:
            print(f"Embedding batch failed after retries: {exc}")
            for row in batch:
                _mark_chunk_failed(row["id"])


def process_document(document_id: UUID, file_path: str, file_type: str):
    try:
        text, page_count = extract_text(file_path, file_type)

        if not text.strip():
            _update_document_status(
                document_id,
                "failed",
                page_count=page_count,
                error_message="No extractable text found in file.",
            )
            return

        chunks = split_into_chunks(
            text,
            chunk_token_size=CHUNK_TOKEN_SIZE,
            overlap_tokens=CHUNK_TOKEN_OVERLAP,
        )

        saved_chunks = _insert_chunks(document_id, chunks)
        _update_document_status(document_id, "processing", page_count=page_count)

        embed_chunks(saved_chunks)

        remaining = _count_not_ready(document_id)
        if remaining == 0:
            _update_document_status(document_id, "ready", page_count=page_count)
        else:
            _update_document_status(
                document_id,
                "processing",
                page_count=page_count,
                error_message=(
                    f"{remaining} chunk(s) failed to embed and are pending reprocessing."
                ),
            )

    except Exception as exc:
        print(f"Processing failed for document {document_id}: {exc}")
        _update_document_status(
            document_id,
            "failed",
            error_message=str(exc),
        )


def reprocess_failed_chunks():
    with connect_to_database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, document_id, text
                FROM chunks
                WHERE embedding_status = 'failed'
                  AND embedding_attempts < 5
                ORDER BY created_at ASC
                LIMIT 50
                """
            )
            failed = [
                {"id": row[0], "document_id": row[1], "text": row[2]}
                for row in cursor.fetchall()
            ]

    embed_chunks(failed)

    document_ids = {row["document_id"] for row in failed}
    for document_id in document_ids:
        remaining = _count_not_ready(document_id)
        if remaining == 0:
            _update_document_status(document_id, "ready")

    return {"reprocessed": len(failed)}
