import os
import unicodedata
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from api.deps import get_app_state, get_session, AppState
from core.domain.project import Project
from core.domain.settings import Settings
from core.sync.folder_scanner import DEFAULT_IGNORE_PATTERNS

router = APIRouter(prefix="/vault", tags=["vault"])


class TreeNode(BaseModel):
    path: str = Field(..., description="Relative path from vault root")
    name: str = Field(..., description="Directory name")
    is_dir: bool = True
    children: list["TreeNode"] = Field(default_factory=list)


_ = TreeNode.model_rebuild()


class TreeResponse(BaseModel):
    root: str = Field(..., description="Absolute path to vault root")
    nodes: list[TreeNode]


def build_directory_tree(
    current_abs_path: Path, vault_root: Path, ignore_patterns: set[str]
) -> list[TreeNode]:
    nodes = []
    try:
        with os.scandir(current_abs_path) as entries:
            for entry in entries:
                if entry.is_dir():
                    name = entry.name
                    if name.startswith(".") or name in ignore_patterns:
                        continue

                    abs_path = Path(entry.path)
                    try:
                        rel_path = abs_path.relative_to(vault_root)
                    except ValueError:
                        continue

                    node = TreeNode(
                        path=str(rel_path),
                        name=name,
                        is_dir=True,
                        children=build_directory_tree(
                            abs_path, vault_root, ignore_patterns
                        ),
                    )
                    nodes.append(node)
    except (PermissionError, FileNotFoundError):
        pass

    nodes.sort(key=lambda x: getattr(x, "name", ""))
    return nodes


class DocumentResponse(BaseModel):
    filename: str = Field(..., description="File name")
    content: str = Field(..., description="Raw markdown content")


def _get_vault_root(
    app_state: AppState,
    db: Session,
) -> Path:
    """Settings의 vault_path 우선, 없으면 syncer의 root_path 사용."""
    db_settings = db.get(Settings, 1)
    if db_settings and db_settings.vault_path:
        p = Path(db_settings.vault_path)
        if p.is_dir():
            return p
    return app_state.syncer.folder_scanner.root_path


def _normalize_unicode(s: str) -> str:
    """NFC 정규화 (macOS NFD 호환)."""
    return unicodedata.normalize("NFC", s)


def _find_file_by_relative_path(
    vault_root: Path,
    relative_path: str,
) -> Optional[Path]:
    """relative_path로 직접 파일 조회. Unicode 정규화 폴백 포함."""
    # 1차: 직접 조합
    direct = vault_root / relative_path
    if direct.is_file():
        return direct

    # 2차: NFC 정규화 후 시도
    nfc_path = vault_root / _normalize_unicode(relative_path)
    if nfc_path.is_file():
        return nfc_path

    # 3차: NFD 정규화 후 시도
    nfd_path = vault_root / unicodedata.normalize("NFD", relative_path)
    if nfd_path.is_file():
        return nfd_path

    return None


def _find_file_by_filename(
    vault_root: Path,
    filename: str,
) -> Optional[Path]:
    """파일명으로 rglob 검색. Unicode 정규화 폴백 포함."""
    # 1차: 원본 파일명
    matches = [m for m in vault_root.rglob(filename) if m.is_file()]
    if matches:
        return matches[0]

    # 2차: NFC 정규화
    nfc_name = _normalize_unicode(filename)
    if nfc_name != filename:
        matches = [m for m in vault_root.rglob(nfc_name) if m.is_file()]
        if matches:
            return matches[0]

    # 3차: NFD 정규화
    nfd_name = unicodedata.normalize("NFD", filename)
    if nfd_name != filename and nfd_name != nfc_name:
        matches = [m for m in vault_root.rglob(nfd_name) if m.is_file()]
        if matches:
            return matches[0]

    return None


@router.get("/document", response_model=DocumentResponse)
def get_vault_document(
    source: str = Query(..., description="File name to look up (e.g. 'note.md')"),
    relative_path: Optional[str] = Query(
        default=None,
        description="Relative path from vault root (preferred over source)",
    ),
    app_state: AppState = Depends(get_app_state),
    db: Session = Depends(get_session),
):
    """
    Returns the raw markdown content of a vault document.

    Lookup priority:
    1. relative_path (direct path join — fast & accurate)
    2. source filename (rglob fallback)
    Both include Unicode normalization fallbacks for macOS NFD compatibility.
    """
    vault_root = _get_vault_root(app_state, db)

    file_path: Optional[Path] = None

    # Priority 1: relative_path 직접 조회
    if relative_path:
        file_path = _find_file_by_relative_path(vault_root, relative_path)

    # Priority 2: source 파일명으로 rglob 폴백
    if file_path is None:
        file_path = _find_file_by_filename(vault_root, source)

    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{source}' not found in vault",
        )

    # Security: ensure the file is within the vault root
    try:
        file_path.resolve().relative_to(vault_root.resolve())
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Access denied: file is outside vault root",
        )

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read document: {str(e)}",
        )

    return DocumentResponse(filename=source, content=content)


@router.get("/tree", response_model=TreeResponse)
def get_vault_tree(
    project_id: int | None = Query(None, description="Project ID to scan (optional)"),
    session: Session = Depends(get_session),
    app_state: AppState = Depends(get_app_state),
):
    """
    Returns a recursive directory tree.
    If project_id is provided, scans that project's path.
    If project_id is None, scans the entire Vault Root.
    """
    vault_root = _get_vault_root(app_state, session)

    if project_id is not None:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=404, detail=f"Project with ID {project_id} not found"
            )
        project_abs_path = (vault_root / project.path).resolve()
        relative_path_start = project.path
    else:
        # Global Vault Mode
        project_abs_path = vault_root
        relative_path_start = ""

    if not project_abs_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Path does not exist on disk: {project_abs_path}",
        )
    if not project_abs_path.is_dir():
        raise HTTPException(
            status_code=400, detail=f"Path is not a directory: {project_abs_path}"
        )

    root_node = TreeNode(
        path=relative_path_start,
        name=project_abs_path.name,
        is_dir=True,
        children=build_directory_tree(
            project_abs_path, vault_root, DEFAULT_IGNORE_PATTERNS
        ),
    )

    return TreeResponse(root=str(vault_root), nodes=[root_node])
