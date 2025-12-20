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
from loguru import logger

from synth_lab.api.errors import register_exception_handlers
from synth_lab.infrastructure.config import API_HOST, API_PORT, ensure_directories


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting synth-lab API...")
    ensure_directories()
    logger.info(f"API ready at http://{API_HOST}:{API_PORT}")
    yield
    # Shutdown
    logger.info("Shutting down synth-lab API...")


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
from synth_lab.api.routers import synths, research, topics, prfaq

# Register routers
app.include_router(synths.router, prefix="/synths", tags=["synths"])
app.include_router(research.router, prefix="/research", tags=["research"])
app.include_router(topics.router, prefix="/topics", tags=["topics"])
app.include_router(prfaq.router, prefix="/prfaq", tags=["prfaq"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=API_HOST, port=API_PORT)
