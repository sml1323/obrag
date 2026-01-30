from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from core.domain.project import Project

class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    name: str = Field(..., min_length=1, max_length=100)
    path: str = Field(..., min_length=1)
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    progress: Optional[int] = Field(None, ge=0, le=100, description="Project progress (0-100)")

class ProjectRead(Project):
    """Schema for reading project details with computed status."""
    is_stale: bool
    days_inactive: int
