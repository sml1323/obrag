from importlib import import_module
from pathlib import Path
from typing import Any

import chromadb
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sklearn.manifold import TSNE  # type: ignore[import-untyped]

from api.deps import AppState, get_app_state


def _model_manager():
    return import_module("core.embedding.model_manager")


router = APIRouter(prefix="/embedding", tags=["embedding"])


class ModelStatusResponse(BaseModel):
    model_id: str
    status: str
    progress: float
    size_mb: int | None = None
    error: str | None = None
    local_path: str | None = None


class ModelListItem(BaseModel):
    model_id: str
    size_mb: int | None = None
    dimension: int | None = None
    status: str
    is_cached: bool


class ModelListResponse(BaseModel):
    models: list[ModelListItem]


class DownloadRequest(BaseModel):
    model_id: str


class DownloadResponse(BaseModel):
    model_id: str
    status: str
    message: str


@router.get("/models", response_model=ModelListResponse)
async def get_available_models():
    model_manager = _model_manager()
    models = model_manager.list_available_models()
    return ModelListResponse(models=[ModelListItem(**model) for model in models])


@router.get("/models/{model_id:path}/status", response_model=ModelStatusResponse)
async def get_model_status(model_id: str):
    model_manager = _model_manager()
    info = model_manager.get_model_info(model_id)
    return ModelStatusResponse(
        model_id=info.model_id,
        status=info.status.value,
        progress=info.progress,
        size_mb=info.size_mb,
        error=info.error,
        local_path=info.local_path,
    )


@router.post("/models/download", response_model=DownloadResponse)
async def start_model_download(request: DownloadRequest):
    model_manager = _model_manager()
    info = model_manager.get_model_info(request.model_id)

    if info.status == model_manager.ModelStatus.READY:
        return DownloadResponse(
            model_id=request.model_id,
            status="ready",
            message="Model is already downloaded",
        )

    if info.status == model_manager.ModelStatus.DOWNLOADING:
        return DownloadResponse(
            model_id=request.model_id,
            status="downloading",
            message="Download already in progress",
        )

    model_manager.download_model_async(request.model_id)

    return DownloadResponse(
        model_id=request.model_id,
        status="started",
        message="Download started in background",
    )


@router.delete("/models/{model_id:path}/download-state")
async def cancel_download(model_id: str):
    model_manager = _model_manager()
    model_manager.clear_download_state(model_id)
    return {"status": "cleared", "model_id": model_id}


class CollectionInfo(BaseModel):
    name: str
    count: int
    model_name: str | None = None


class CollectionListResponse(BaseModel):
    collections: list[CollectionInfo]


class VectorPoint(BaseModel):
    id: str
    x: float
    y: float
    z: float | None = None
    text: str
    source: str | None = None
    metadata: dict[str, Any]


class VectorVisualizationResponse(BaseModel):
    collection_name: str
    total_count: int
    points: list[VectorPoint]
    categories: list[str]
    dimensions: int = 3


def _extract_model_from_collection_name(collection_name: str) -> str | None:
    if collection_name == "obsidian_notes":
        return None
    prefixes = ["obsidian_notes_", "obsidian_"]
    for prefix in prefixes:
        if collection_name.startswith(prefix):
            return collection_name[len(prefix) :]
    return None


@router.get("/collections", response_model=CollectionListResponse)
async def list_collections(app_state: AppState = Depends(get_app_state)):
    chroma_db_path = Path(app_state.chroma_store.persist_path)

    if not chroma_db_path.exists():
        return CollectionListResponse(collections=[])

    client = chromadb.PersistentClient(path=str(chroma_db_path))
    collections = client.list_collections()

    result: list[CollectionInfo] = []
    for col in collections:
        model_name = _extract_model_from_collection_name(col.name)
        result.append(
            CollectionInfo(
                name=col.name,
                count=col.count(),
                model_name=model_name,
            )
        )

    return CollectionListResponse(collections=result)


@router.get(
    "/collections/{collection_name}/vectors", response_model=VectorVisualizationResponse
)
async def get_collection_vectors(
    collection_name: str,
    limit: int = Query(default=500, le=2000),
    perplexity: int = Query(default=30, ge=5, le=50),
    dimensions: int = Query(default=3, ge=2, le=3),
    app_state: AppState = Depends(get_app_state),
):
    chroma_db_path = Path(app_state.chroma_store.persist_path)

    if not chroma_db_path.exists():
        raise HTTPException(status_code=404, detail="ChromaDB not found")

    client = chromadb.PersistentClient(path=str(chroma_db_path))

    existing_names = [c.name for c in client.list_collections()]
    if collection_name not in existing_names:
        raise HTTPException(
            status_code=404, detail=f"Collection '{collection_name}' not found"
        )

    collection = client.get_collection(collection_name)
    total_count = collection.count()

    if total_count == 0:
        return VectorVisualizationResponse(
            collection_name=collection_name,
            total_count=0,
            points=[],
            categories=[],
            dimensions=dimensions,
        )

    result = collection.get(
        include=["embeddings", "documents", "metadatas"],
        limit=limit,
    )

    embeddings = result.get("embeddings")
    documents = result.get("documents") or []
    metadatas = result.get("metadatas") or []
    ids = result.get("ids") or []

    if embeddings is None or len(ids) == 0:
        return VectorVisualizationResponse(
            collection_name=collection_name,
            total_count=total_count,
            points=[],
            categories=[],
            dimensions=dimensions,
        )

    vectors = np.array(embeddings)

    effective_perplexity = min(perplexity, len(vectors) - 1, 30)
    if effective_perplexity < 5:
        effective_perplexity = min(5, len(vectors) - 1)

    if len(vectors) < 4:
        reduced = np.random.randn(len(vectors), dimensions)
    else:
        tsne = TSNE(
            n_components=dimensions, random_state=42, perplexity=effective_perplexity
        )
        reduced = tsne.fit_transform(vectors)

    categories: set[str] = set()
    points: list[VectorPoint] = []

    for i, doc_id in enumerate(ids):
        metadata = (
            dict(metadatas[i]) if metadatas is not None and i < len(metadatas) else {}
        )
        text = documents[i] if documents is not None and i < len(documents) else ""
        relative_path = str(
            metadata.get("relative_path") or metadata.get("source") or ""
        )

        category = relative_path.split("/")[0] if "/" in relative_path else "unknown"
        categories.add(category)

        points.append(
            VectorPoint(
                id=doc_id,
                x=float(reduced[i, 0]),
                y=float(reduced[i, 1]),
                z=float(reduced[i, 2]) if dimensions == 3 else None,
                text=text[:200] if text else "",
                source=relative_path,
                metadata=metadata,
            )
        )

    return VectorVisualizationResponse(
        collection_name=collection_name,
        total_count=total_count,
        points=points,
        categories=sorted(categories),
        dimensions=dimensions,
    )
