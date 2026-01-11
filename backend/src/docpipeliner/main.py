"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from docpipeliner import __version__
from docpipeliner.api.routes import analytics, documents, health, reviews
from docpipeliner.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    logger.info(f"Starting DocPipeliner v{__version__}")
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")

    yield

    # Shutdown
    logger.info("Shutting down DocPipeliner")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Intelligent Document Processing Pipeline with multi-engine OCR",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(
        documents.router,
        prefix=settings.api_prefix,
    )
    app.include_router(
        reviews.router,
        prefix=settings.api_prefix,
    )
    app.include_router(
        analytics.router,
        prefix=settings.api_prefix,
    )

    return app


# Create application instance
app = create_app()


def main():
    """Run the application with uvicorn."""
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "docpipeliner.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )


if __name__ == "__main__":
    main()
