from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from api.deps import get_session, get_chroma_store
from api.schemas.para import ParaProjectRead
from core.domain.settings import Settings
from core.sync.sync_registry import load_registry
from db.chroma_store import ChromaStore, derive_collection_name

router = APIRouter(prefix="/para", tags=["para"])


def _normalize_relative_path(path_str: str) -> str:
    return path_str.replace("\\", "/").lstrip("./")


def _resolve_para_root(vault_root: Path, para_root: str) -> Optional[str]:
    raw = para_root.strip()
    if not raw:
        return None
    root_path = Path(raw)
    if root_path.is_absolute():
        try:
            root_path = root_path.resolve().relative_to(vault_root.resolve())
        except ValueError:
            return None
    rel = root_path.as_posix().strip("/")
    return rel or None


def _find_registry_path(
    chroma_store: ChromaStore,
    vault_root: Path,
    collection_name: str,
) -> Optional[Path]:
    candidates = [
        chroma_store.persist_path / f".sync_registry_{collection_name}.json",
        vault_root / f".sync_registry_{collection_name}.json",
        vault_root / ".sync_registry.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


@router.get("/projects", response_model=List[ParaProjectRead])
def list_para_projects(
    session: Session = Depends(get_session),
    chroma_store: ChromaStore = Depends(get_chroma_store),
):
    settings = session.get(Settings, 1)
    if not settings or not settings.vault_path or not settings.para_root_path:
        return []

    vault_root = Path(settings.vault_path)
    if not vault_root.exists() or not vault_root.is_dir():
        raise HTTPException(status_code=400, detail="Vault path does not exist")

    para_root_rel = _resolve_para_root(vault_root, settings.para_root_path)
    if not para_root_rel:
        return []

    model_name = settings.embedding_model or "text-embedding-3-small"
    collection_name = derive_collection_name("obsidian_notes", model_name)
    registry_path = _find_registry_path(chroma_store, vault_root, collection_name)

    if registry_path is None:
        return []

    registry = load_registry(registry_path)
    prefix = f"{para_root_rel}/"

    projects: Dict[str, dict] = {}

    for rel_path, info in registry.files.items():
        normalized = _normalize_relative_path(rel_path)
        if not normalized.startswith(prefix):
            continue
        remainder = normalized[len(prefix) :]
        parts = remainder.split("/")
        if len(parts) < 2:
            # 프로젝트 폴더 바로 아래 파일은 제외
            continue

        project_name = parts[0]
        project_path = f"{para_root_rel}/{project_name}"

        mtime = info.get("mtime")
        if not mtime:
            continue

        last_modified = datetime.fromtimestamp(mtime, tz=timezone.utc)
        file_name = parts[-1]

        project = projects.setdefault(
            project_path,
            {
                "id": project_path,
                "name": project_name,
                "path": project_path,
                "file_count": 0,
                "last_modified_at": None,
                "files": [],
            },
        )

        project["files"].append(
            {
                "id": normalized,
                "name": file_name,
                "relative_path": normalized,
                "last_modified_at": last_modified,
            }
        )

        if (
            project["last_modified_at"] is None
            or last_modified > project["last_modified_at"]
        ):
            project["last_modified_at"] = last_modified

    results: List[ParaProjectRead] = []
    for project in projects.values():
        project["file_count"] = len(project["files"])
        project["files"].sort(key=lambda f: f["last_modified_at"], reverse=True)
        results.append(ParaProjectRead(**project))

    results.sort(
        key=lambda p: p.last_modified_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return results
