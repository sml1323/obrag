from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel

class Project(SQLModel, table=True):
    """
    Project Entity
    
    Represents a folder within the vault that is designated as a 'Project'.
    Projects are identified strictly by their relative path within the vault.
    """
    # Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Core Definition
    name: str = Field(index=True, description="Display name of the project")
    path: str = Field(unique=True, index=True, description="Relative path in the vault (e.g. 'Study/CS101')")
    description: Optional[str] = Field(default=None, description="Optional description of the project")

    # Status
    is_active: bool = Field(default=True, description="Whether the project is active (not archived)")

    # Metadata
    last_modified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last modification time of files in the project")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When this project was registered")
    
    progress: int = Field(default=0, description="Project progress (0-100)")
    file_count: int = Field(default=0, description="Number of markdown files in the project")
