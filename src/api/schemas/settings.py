from typing import Optional
from pydantic import BaseModel
from core.domain.settings import Settings


class SettingsUpdate(BaseModel):
    vault_path: Optional[str] = None
    para_root_path: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_api_key: Optional[str] = None
    ollama_endpoint: Optional[str] = None


class SettingsResponse(Settings):
    pass
