from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlmodel import Session

from api.deps import get_syncer, get_session, get_chroma_store
from core.sync.incremental_syncer import IncrementalSyncer, SyncResult, create_syncer
from core.domain.project import Project
from core.domain.settings import Settings
from core.embedding import OpenAIEmbedder
from db.chroma_store import ChromaStore

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/trigger", response_model=SyncResult)
def trigger_sync(
    project_id: int | None = Query(default=None),
    embedding_api_key: Optional[str] = Body(default=None, embed=True),
    include_paths: Optional[List[str]] = Body(default=None, embed=True),
    syncer: IncrementalSyncer = Depends(get_syncer),
    session: Session = Depends(get_session),
    chroma_store: ChromaStore = Depends(get_chroma_store),
):
    if project_id is None:
        active_store = chroma_store
        if embedding_api_key:
            embedder = OpenAIEmbedder(api_key=embedding_api_key)
            active_store = ChromaStore(
                persist_path=str(chroma_store.persist_path),
                collection_name=chroma_store.collection_name,
                embedder=embedder,
            )

        db_settings = session.get(Settings, 1)
        if db_settings and db_settings.vault_path:
            root_path = Path(db_settings.vault_path)
            if not root_path.is_dir():
                raise HTTPException(status_code=400, detail="Vault path does not exist")
            dynamic_syncer = create_syncer(
                root_path=str(root_path),
                chroma_store=active_store,
                include_paths=include_paths,
            )
            return dynamic_syncer.sync()

        if include_paths:
            syncer.folder_scanner.include_paths = include_paths
        return syncer.sync()

    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_path = Path(project.path)
    if not project_path.is_dir():
        raise HTTPException(status_code=400, detail="Project path does not exist")

    active_store = chroma_store
    if embedding_api_key:
        embedder = OpenAIEmbedder(api_key=embedding_api_key)
        active_store = ChromaStore(
            persist_path=str(chroma_store.persist_path),
            collection_name=chroma_store.collection_name,
            embedder=embedder,
        )

    dynamic_syncer = create_syncer(
        root_path=project.path,
        chroma_store=active_store,
        include_paths=include_paths,
    )
    return dynamic_syncer.sync()
