from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ParaFileRead(BaseModel):
    id: str
    name: str
    relative_path: str
    last_modified_at: datetime


class ParaProjectRead(BaseModel):
    id: str
    name: str
    path: str
    file_count: int
    last_modified_at: Optional[datetime] = None
    files: List[ParaFileRead]
