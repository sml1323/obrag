from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlmodel import Session, select

from api.deps import get_session
from api.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from core.domain.project import Project
from core.project.status import ProjectStatus

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectRead)
def create_project(project_in: ProjectCreate, session: Session = Depends(get_session)):
    """Register a new project folder."""
    # 1. Check if path exists (optional but recommended)
    # We assume server has access to this path.
    # In a real desktop app, we might need more complex validation.
    # For now, we trust the input, but we could add:
    # if not Path(project_in.path).exists():
    #     raise HTTPException(status_code=400, detail="Path does not exist")
    
    # 2. Duplicate check
    existing = session.exec(select(Project).where(Project.path == project_in.path)).first()
    if existing:
         raise HTTPException(status_code=400, detail="Project path already registered")

    project = Project.model_validate(project_in)
    session.add(project)
    session.commit()
    session.refresh(project)
    
    is_stale, days_inactive = ProjectStatus.calculate_staleness(project)
    
    return ProjectRead(
        **project.model_dump(),
        is_stale=is_stale,
        days_inactive=days_inactive
    )

@router.get("/", response_model=List[ProjectRead])
def list_projects(
    session: Session = Depends(get_session),
    active_only: bool = Query(True, description="Filter active projects"),
    stale_only: bool = Query(False, description="Filter stale projects (>30 days inactive)")
):
    """List all projects with status."""
    query = select(Project)
    if active_only:
        query = query.where(Project.is_active == True)
        
    projects = session.exec(query).all()
    
    results = []
    for p in projects:
        is_stale, days_inactive = ProjectStatus.calculate_staleness(p)
        
        if stale_only and not is_stale:
            continue
            
        results.append(ProjectRead(
            **p.model_dump(),
            is_stale=is_stale,
            days_inactive=days_inactive
        ))
        
    return results

@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, session: Session = Depends(get_session)):
    """Get project details."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    is_stale, days_inactive = ProjectStatus.calculate_staleness(project)
    
    return ProjectRead(
        **project.model_dump(),
        is_stale=is_stale,
        days_inactive=days_inactive
    )

@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: int, project_in: ProjectUpdate, session: Session = Depends(get_session)):
    """Update project info."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    update_data = project_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
        
    session.add(project)
    session.commit()
    session.refresh(project)
    
    is_stale, days_inactive = ProjectStatus.calculate_staleness(project)
    
    return ProjectRead(
        **project.model_dump(),
        is_stale=is_stale,
        days_inactive=days_inactive
    )

@router.delete("/{project_id}")
def delete_project(project_id: int, session: Session = Depends(get_session)):
    """Delete a project."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    session.delete(project)
    session.commit()
    return {"ok": True}
