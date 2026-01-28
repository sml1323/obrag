from fastapi import APIRouter, Depends
from api.deps import get_chroma_store
from db.chroma_store import ChromaStore

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Liveness Probe"""
    return {"status": "healthy"}

@router.get("/status")
async def get_status(store: ChromaStore = Depends(get_chroma_store)):
    """Readiness Probe & Stats"""
    return {
        "status": "ready",
        "db": store.get_stats(),
    }
