import os

import jwt
from dotenv import load_dotenv
from fastapi import Request
from fastapi.responses import JSONResponse

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

PUBLIC_PATHS = {
    "/api/health",
    "/api/auth/register",
    "/api/auth/login",
    "/docs",
    "/openapi.json",
    "/redoc",
}

PROTECTED_PREFIXES = (
    "/api/auth/",
    "/api/documents",
)


async def auth_middleware(request: Request, call_next):
    path = request.url.path

    protected = (
        path.startswith("/api/auth/")
        or path.startswith("/api/documents")
        or path == "/api/search"
    )

    if path in PUBLIC_PATHS or not protected:
        return await call_next(request)

    authorization = request.headers.get("Authorization")

    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Authentication required"},
        )

    token = authorization.split(" ", 1)[1]

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        request.state.user = payload

    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Token has expired"},
        )

    except jwt.InvalidTokenError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid token"},
        )

    return await call_next(request)
