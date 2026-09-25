from fastapi import APIRouter, BackgroundTasks, Depends, Request, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from uuid import UUID

from controllers.document_controller import (
    delete_document,
    get_document,
    list_documents,
    upload_document,
)

router = APIRouter(prefix="/api/documents")
bearer_scheme = HTTPBearer(auto_error=False)


def _user_id(request: Request) -> int:
    try:
        return int(request.state.user["user_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Authenticated user information is missing.") from exc


@router.post("", status_code=202)
async def upload(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    return await upload_document(background_tasks, file, _user_id(request))


@router.get("")
def list_all(
    request: Request,
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    return list_documents(_user_id(request))


@router.get("/{document_id}")
def get_one(
    document_id: UUID,
    request: Request,
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    return get_document(document_id, _user_id(request))


@router.delete("/{document_id}", status_code=204)
def remove(
    document_id: UUID,
    request: Request,
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    delete_document(document_id, _user_id(request))
    return None
