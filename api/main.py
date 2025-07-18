"""
FastAPI Main Application for Nutrition Bot
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import load_dotenv

from api.config import settings
from api.routers import health, motor1, motor2, motor3
from api.services.chromadb_service import ChromaDBService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting Nutrition Bot API...")
    
    # Initialize ChromaDB service
    try:
        app.state.chromadb = ChromaDBService()
        logger.info("ChromaDB service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Nutrition Bot API...")


# Create FastAPI app
app = FastAPI(
    title="Nutrition Bot API",
    description="API for automated nutrition plan generation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(motor1.router, prefix="/api/v1/motor1", tags=["motor1"])
app.include_router(motor2.router, prefix="/api/v1/motor2", tags=["motor2"])
app.include_router(motor3.router, prefix="/api/v1/motor3", tags=["motor3"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Nutrition Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=settings.api_workers
    )