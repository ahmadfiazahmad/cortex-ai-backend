from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

UPLOAD_DIR = Path("uploads")
MAX_UPLOAD_SIZE_MB = 20
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_MIME_TYPES = {
    "application/pdf": ("pdf", ".pdf"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
        "docx",
        ".docx",
    ),
    "text/plain": ("txt", ".txt"),
}


def ensure_upload_directory() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_upload_file(upload_file: UploadFile) -> tuple[str, str]:
    file_type_info = ALLOWED_MIME_TYPES.get(upload_file.content_type or "")
    if not file_type_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PDF, DOCX, and TXT files are allowed.",
        )

    file_type, extension = file_type_info
    ensure_upload_directory()

    destination = UPLOAD_DIR / f"{uuid4().hex}{extension}"
    total_size = 0

    try:
        with destination.open("wb") as output:
            while chunk := await upload_file.read(1024 * 1024):
                total_size += len(chunk)

                if total_size > MAX_UPLOAD_SIZE_BYTES:
                    destination.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size must not exceed {MAX_UPLOAD_SIZE_MB} MB.",
                    )

                output.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store uploaded file.",
        ) from exc
    finally:
        await upload_file.close()

    return str(destination), file_type
