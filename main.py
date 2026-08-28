from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware.error_handler import global_exception_handler
from middleware.request_logger import request_logger
from routes.health import router

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


app.add_exception_handler(Exception, global_exception_handler)
app.middleware("http")(request_logger)
app.include_router(router)