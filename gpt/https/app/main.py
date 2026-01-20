import logging
from fastapi import FastAPI
from app.config import settings
from app.routes import router


def create_app() -> FastAPI:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = FastAPI(
        title=settings.app_name,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.include_router(router)

    @app.on_event("startup")
    async def startup_event():
        logging.info("Application startup complete")

    @app.on_event("shutdown")
    async def shutdown_event():
        logging.info("Application shutdown complete")

    return app


app = create_app()
