from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlmodel import Session

from api.deps import get_syncer, get_session, get_chroma_store
from core.sync.incremental_syncer import IncrementalSyncer, SyncResult, create_syncer
from core.domain.project import Project
from core.domain.settings import Settings
from core.embedding import EmbedderFactory
from config.models import (
    OpenAIEmbeddingConfig,
    OllamaEmbeddingConfig,
    SentenceTransformerEmbeddingConfig,
)
from db.chroma_store import ChromaStore, derive_collection_name

router = APIRouter(prefix="/sync", tags=["sync"])


def _create_embedder_from_settings(settings: Settings):
    provider = (settings.embedding_provider or "openai").lower()
    model = settings.embedding_model or ""

    if provider == "ollama":
        if not model:
            model = "nomic-embed-text"
        config = OllamaEmbeddingConfig(
            model_name=model,
            base_url=settings.ollama_endpoint or "http://localhost:11434",
        )
    elif provider == "sentence_transformers":
        if not model:
            model = "BAAI/bge-m3"
        config = SentenceTransformerEmbeddingConfig(model_name=model)
    else:
        if not model:
            model = "text-embedding-3-small"
        api_key = settings.embedding_api_key or settings.llm_api_key
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="OpenAI embedding requires API key. Please configure it in Settings.",
            )
        if not api_key.startswith("sk-"):
            raise HTTPException(
                status_code=400,
                detail="Invalid OpenAI API key format. API key must start with 'sk-'. Please update in Settings.",
            )
        config = OpenAIEmbeddingConfig(
            model_name=model,  # type: ignore
            api_key=api_key,
        )

    try:
        embedder = EmbedderFactory.create(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return embedder, model


def _create_store_for_settings(
    settings: Settings,
    base_persist_path: str,
    base_collection_name: str = "obsidian_notes",
) -> ChromaStore:
    """
    Settings 기반으로 ChromaStore 생성.

    임베딩 모델별로 다른 collection을 사용합니다.
    """
    embedder, model_name = _create_embedder_from_settings(settings)
    collection_name = derive_collection_name(base_collection_name, model_name)

    return ChromaStore(
        persist_path=base_persist_path,
        collection_name=collection_name,
        embedder=embedder,
    )


@router.post("/trigger", response_model=SyncResult)
def trigger_sync(
    project_id: int | None = Query(default=None),
    force_reindex: bool = Query(
        default=False, description="전체 재인덱싱 (기존 데이터 삭제)"
    ),
    include_paths: Optional[List[str]] = Body(default=None, embed=True),
    syncer: IncrementalSyncer = Depends(get_syncer),
    session: Session = Depends(get_session),
    chroma_store: ChromaStore = Depends(get_chroma_store),
):
    """
    동기화 트리거.

    Args:
        project_id: 특정 프로젝트만 동기화 (없으면 vault 전체)
        force_reindex: True면 전체 재인덱싱 (기존 벡터 삭제 후 재생성)
        include_paths: 포함할 폴더 경로 목록
    """
    db_settings = session.get(Settings, 1)

    if project_id is None:
        if db_settings and db_settings.vault_path:
            root_path = Path(db_settings.vault_path)
            if not root_path.is_dir():
                raise HTTPException(status_code=400, detail="Vault path does not exist")

            active_store = _create_store_for_settings(
                db_settings,
                str(chroma_store.persist_path),
            )

            registry_path = (
                chroma_store.persist_path
                / f".sync_registry_{active_store.collection_name}.json"
            )

            dynamic_syncer = create_syncer(
                root_path=str(root_path),
                chroma_store=active_store,
                registry_path=registry_path,
                include_paths=include_paths,
            )

            current_vault = str(root_path.resolve())
            stored_vault = dynamic_syncer.registry.get_vault_path()
            vault_changed = stored_vault is not None and stored_vault != current_vault

            # Path integrity check: verify registry paths actually exist on disk.
            # If vault_path matches but paths have a stale prefix (e.g. "note/1.PARA/..."
            # instead of "1.PARA/..."), the registry is corrupted and needs full_sync.
            paths_corrupted = False
            if not vault_changed and len(dynamic_syncer.registry.files) > 0:
                resolved_root = root_path.resolve()
                sample_keys = list(dynamic_syncer.registry.files.keys())[:5]
                valid_count = sum(
                    1 for k in sample_keys if (resolved_root / k).exists()
                )
                if valid_count == 0:
                    paths_corrupted = True

            if vault_changed or force_reindex or paths_corrupted:
                result = dynamic_syncer.full_sync()
            else:
                result = dynamic_syncer.sync()

            dynamic_syncer.registry.set_vault_path(current_vault)
            dynamic_syncer.registry.save()
            return result

        if include_paths:
            syncer.folder_scanner.include_paths = include_paths

        if force_reindex:
            return syncer.full_sync()
        return syncer.sync()

    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_path = Path(project.path)
    if not project_path.is_dir():
        raise HTTPException(status_code=400, detail="Project path does not exist")

    if db_settings:
        active_store = _create_store_for_settings(
            db_settings,
            str(chroma_store.persist_path),
        )
    else:
        active_store = chroma_store

    dynamic_syncer = create_syncer(
        root_path=project.path,
        chroma_store=active_store,
        include_paths=include_paths,
    )

    if force_reindex:
        return dynamic_syncer.full_sync()
    return dynamic_syncer.sync()
