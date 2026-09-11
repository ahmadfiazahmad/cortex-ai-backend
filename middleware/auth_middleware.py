import os

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse

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


async def auth_middleware(request: Request, call_next):
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    if not request.url.path.startswith("/api/auth/"):
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