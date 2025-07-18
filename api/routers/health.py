"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import chromadb
from api.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {}
    }
    
    # Check ChromaDB
    try:
        client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
        collection = client.get_collection(settings.chroma_collection_name)
        doc_count = collection.count()
        health_status["components"]["chromadb"] = {
            "status": "healthy",
            "documents": doc_count
        }
    except Exception as e:
        health_status["components"]["chromadb"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Redis (if available)
    try:
        import redis
        r = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=settings.redis_decode_responses
        )
        r.ping()
        health_status["components"]["redis"] = {
            "status": "healthy"
        }
    except Exception as e:
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        # Redis is optional, so don't degrade overall status
    
    return health_status