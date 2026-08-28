from fastapi import Request


async def request_logger(request: Request, call_next):
    print(f"{request.method} {request.url.path}")

    response = await call_next(request)

    return response