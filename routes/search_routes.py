from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from controllers.search_controller import search_documents
from models.search import SearchRequest

router = APIRouter(prefix="/api/search")
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("")
def search(
    payload: SearchRequest,
    request: Request,
    _: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    try:
        user_id = int(request.state.user["user_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Authenticated user information is missing.") from exc

    return search_documents(payload, user_id)
