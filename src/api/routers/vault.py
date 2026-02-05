import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from api.deps import get_app_state, get_session, AppState
from core.domain.project import Project
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
    vault_root = app_state.syncer.folder_scanner.root_path
    
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
