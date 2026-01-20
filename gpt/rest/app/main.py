from fastapi import FastAPI
from .config import settings
from .api import router
from .logging import setup_logging

setup_logging()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
)

@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}

app.include_router(router, prefix="/api", tags=["api"])
