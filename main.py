from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.database import connect_to_database
from middleware.auth_middleware import auth_middleware
from middleware.error_handler import global_exception_handler
from middleware.request_logger import request_logger
from routes.auth import router as auth_router
from routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        connection = connect_to_database()
        print("Database connected successfully!")
        connection.close()
    except Exception as e:
        print(f"Database connection failed: {e}")

    yield


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.add_exception_handler(Exception, global_exception_handler)

app.middleware("http")(request_logger)
app.middleware("http")(auth_middleware)

app.include_router(health_router)
app.include_router(auth_router)