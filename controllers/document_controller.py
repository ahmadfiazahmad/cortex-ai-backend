import os
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, HTTPException

from config.database import connect_to_database
from middleware.upload import save_upload_file
from services.processing_service import process_document


def _row_to_document(row):
    return {
        "id": row[0],
        "filename": row[1],
        "fileType": row[2],
        "status": row[3],
        "pageCount": row[4],
        "errorMessage": row[5],
        "uploadedAt": row[6],
        "updatedAt": row[7],
    }


async def upload_document(background_tasks: BackgroundTasks, file, user_id: int):
    file_path, file_type = await save_upload_file(file)
    document_id = uuid4()

    try:
        with connect_to_database() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO documents (
                        id, owner_id, filename, file_type, file_path, status
                    )
                    VALUES (%s, %s, %s, %s, %s, 'processing')
                    RETURNING id, filename, file_type, status, uploaded_at
                    """,
                    (
                        document_id,
                        user_id,
                        file.filename or "uploaded-file",
                        file_type,
                        file_path,
                    ),
                )
                row = cursor.fetchone()

        background_tasks.add_task(
            process_document,
            document_id,
            file_path,
            file_type,
        )

        return {
            "id": row[0],
            "filename": row[1],
            "fileType": row[2],
            "status": row[3],
            "uploadedAt": row[4],
        }

    except Exception:
        Path(file_path).unlink(missing_ok=True)
        raise


def list_documents(user_id: int):
    with connect_to_database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, filename, file_type, status, page_count,
                       uploaded_at, updated_at
                FROM documents
                WHERE owner_id = %s
                ORDER BY uploaded_at DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()

    return {
        "documents": [
            {
                "id": row[0],
                "filename": row[1],
                "fileType": row[2],
                "status": row[3],
                "pageCount": row[4],
                "uploadedAt": row[5],
                "updatedAt": row[6],
            }
            for row in rows
        ]
    }


def get_document(document_id: UUID, user_id: int):
    with connect_to_database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, filename, file_type, status, page_count,
                       error_message, uploaded_at, updated_at, file_path
                FROM documents
                WHERE id = %s AND owner_id = %s
                """,
                (document_id, user_id),
            )
            row = cursor.fetchone()

            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            cursor.execute(
                """
                SELECT id, chunk_index, token_count, embedding_status
                FROM chunks
                WHERE document_id = %s
                ORDER BY chunk_index ASC
                """,
                (document_id,),
            )
            chunks = cursor.fetchall()

    return {
        "id": row[0],
        "filename": row[1],
        "fileType": row[2],
        "status": row[3],
        "pageCount": row[4],
        "errorMessage": row[5],
        "uploadedAt": row[6],
        "updatedAt": row[7],
        "chunkCount": len(chunks),
        "chunks": [
            {
                "id": chunk[0],
                "chunkIndex": chunk[1],
                "tokenCount": chunk[2],
                "embeddingStatus": chunk[3],
            }
            for chunk in chunks
        ],
    }


def delete_document(document_id: UUID, user_id: int):
    with connect_to_database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT file_path
                FROM documents
                WHERE id = %s AND owner_id = %s
                """,
                (document_id, user_id),
            )
            row = cursor.fetchone()

            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            cursor.execute(
                "DELETE FROM documents WHERE id = %s AND owner_id = %s",
                (document_id, user_id),
            )

    Path(row[0]).unlink(missing_ok=True)
