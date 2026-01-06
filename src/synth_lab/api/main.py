"""
FastAPI application for synth-lab REST API.

Main application with lifespan events, CORS configuration, and router registration.

References:
    - FastAPI docs: https://fastapi.tiangolo.com/
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from synth_lab.api.errors import register_exception_handlers
from synth_lab.infrastructure.config import (
    API_HOST,
    API_PORT,
    OUTPUT_DIR,
    configure_logging,
    ensure_directories,
)
from synth_lab.infrastructure.database_v2 import get_database_url, init_database_v2
from synth_lab.infrastructure.phoenix_tracing import maybe_setup_tracing, shutdown_tracing


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    configure_logging()
    logger.info("Starting synth-lab API...")
    ensure_directories()
    # Initialize database schema (PostgreSQL via DATABASE_URL)
    db_url = get_database_url()
    logger.info(f"Using database: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    init_database_v2()
    logger.info("Database schema initialized")
    # Setup Phoenix tracing if PHOENIX_ENABLED=true
    maybe_setup_tracing()
    logger.info(f"API ready at http://{API_HOST}:{API_PORT}")
    yield
    # Shutdown
    logger.info("Shutting down synth-lab API...")
    shutdown_tracing()


app = FastAPI(
    title="synth-lab API",
    description="REST API for synthetic persona research platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "synth-lab-api"}


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": "synth-lab API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# Router imports
from synth_lab.api.routers import (
    analysis,
    chat,
    documents,
    experiments,
    exploration,
    insights,
    materials,
    prfaq,
    research,
    synth_groups,
    synths,
    tags,
)

# Register routers
app.include_router(synths.router, prefix="/synths", tags=["synths"])
app.include_router(chat.router, prefix="/synths", tags=["chat"])
app.include_router(research.router, prefix="/research", tags=["research"])
app.include_router(prfaq.router, prefix="/prfaq", tags=["prfaq"])
app.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
app.include_router(analysis.router, prefix="/experiments", tags=["analysis"])
app.include_router(insights.router, prefix="/experiments", tags=["insights"])
app.include_router(documents.router, prefix="/experiments", tags=["documents"])
app.include_router(materials.router, prefix="/experiments", tags=["materials"])
app.include_router(tags.router, prefix="/tags", tags=["tags"])
app.include_router(synth_groups.router, prefix="/synth-groups", tags=["synth-groups"])
app.include_router(exploration.router, prefix="/explorations", tags=["explorations"])

# Mount static files for generated images and documents
# Images available at: /static/document/images/<filename>
STATIC_DIR = OUTPUT_DIR / "document"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static/document", StaticFiles(directory=str(STATIC_DIR)), name="static_documents")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=API_HOST, port=API_PORT)
