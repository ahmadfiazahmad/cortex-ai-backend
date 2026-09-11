from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from controllers.auth_controller import (
    get_user_by_id,
    login_user,
    register_user,
)
from models.user import UserCreate, UserLogin


router = APIRouter(prefix="/api/auth")

bearer_scheme = HTTPBearer()


@router.post("/register")
def register(user: UserCreate):
    return register_user(user)


@router.post("/login")
def login(user: UserLogin):
    return login_user(user)


@router.get("/me")
def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    user_id = request.state.user["user_id"]

    return get_user_by_id(user_id)