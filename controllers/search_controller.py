from fastapi import HTTPException, status

from config.database import connect_to_database
from models.search import SearchRequest
from services.embedding_service import embed_query


def search_documents(payload: SearchRequest, user_id: int):
    query_text = payload.query.strip()
    if not query_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='"query" is required and must be a non-empty string.',
        )

    query_embedding = embed_query(query_text)
    vector_literal = "[" + ",".join(str(value) for value in query_embedding) + "]"

    where_extra = ""
    params = [vector_literal, user_id]

    if payload.documentId:
        where_extra = "AND d.id = %s"
        params.append(payload.documentId)

    params.extend([vector_literal, payload.topK])

    with connect_to_database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    c.id AS chunk_id,
                    c.text,
                    c.chunk_index,
                    d.id AS document_id,
                    d.filename,
                    1 - (c.embedding <=> %s::vector) AS similarity
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE d.owner_id = %s
                  AND c.embedding_status = 'ready'
                  AND c.embedding IS NOT NULL
                  {where_extra}
                ORDER BY c.embedding <=> %s::vector ASC
                LIMIT %s
                """,
                params,
            )
            rows = cursor.fetchall()

    return {
        "query": payload.query,
        "scope": "document" if payload.documentId else "all_documents",
        "results": [
            {
                "chunkId": row[0],
                "text": row[1],
                "chunkIndex": row[2],
                "similarity": float(row[5]),
                "document": {
                    "id": row[3],
                    "filename": row[4],
                },
            }
            for row in rows
        ],
    }
