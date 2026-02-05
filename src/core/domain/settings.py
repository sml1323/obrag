from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class Settings(SQLModel, table=True):
    """
    Global App Settings (Singleton)

    This model persists global configuration such as provider choices,
    API keys, and vault location. By default, only one row with id=1 exists.
    """

    # Singleton pattern: id is always 1
    id: int = Field(default=1, primary_key=True)

    # Core Configuration
    vault_path: Optional[str] = Field(
        default=None, description="Absolute path to the Obsidian vault"
    )
    para_root_path: Optional[str] = Field(
        default=None,
        description="Relative path under vault for PARA projects (e.g. 'Project')",
    )

    # LLM Configuration
    llm_provider: str = Field(
        default="openai", description="Default LLM provider (openai, gemini, ollama)"
    )
    llm_model: str = Field(default="gpt-4o", description="Model name for generation")
    llm_api_key: Optional[str] = Field(
        default=None, description="API Key for LLM provider"
    )

    # Embedding Configuration
    embedding_provider: str = Field(
        default="openai", description="Provider for text embeddings"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small", description="Model name for embeddings"
    )
    embedding_api_key: Optional[str] = Field(
        default=None, description="API Key for embedding provider (if different)"
    )

    # Local LLM (Ollama)
    ollama_endpoint: str = Field(
        default="http://localhost:11434", description="Endpoint for local Ollama server"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When settings were first created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last time settings were updated",
    )

    def mask_api_keys(self) -> "Settings":
        """
        Returns a copy of the settings with API keys partially masked.
        Example: "sk-proj-..." -> "sk-***abc"
        """
        masked = Settings.model_validate(self.model_dump())

        if masked.llm_api_key and len(masked.llm_api_key) > 3:
            masked.llm_api_key = f"***{masked.llm_api_key[-3:]}"
        elif masked.llm_api_key:
            masked.llm_api_key = "***"

        if masked.embedding_api_key and len(masked.embedding_api_key) > 3:
            masked.embedding_api_key = f"***{masked.embedding_api_key[-3:]}"
        elif masked.embedding_api_key:
            masked.embedding_api_key = "***"

        return masked
