from dataclasses import dataclass
from typing import Literal, get_args

Provider = Literal["local", "openai"]
OpenAIEmbeddingModel = Literal["text-embedding-3-small", "text-embedding-3-large"]
LocalEmbeddingModel = Literal["examp"]


@dataclass
class OpenAIEmbeddingConfig:
    provider: Provider = "openai"
    model_name: OpenAIEmbeddingModel = "text-embedding-3-small"
    api_key: str | None = None

    def __post_init__(self):
        if self.provider not in get_args(Provider):
            raise ValueError(f"Invalid provider: {self.provider}")
        if self.model_name not in get_args(OpenAIEmbeddingModel):
            raise ValueError(f"Invalid embedding model: {self.model_name}")
        if self.api_key is not None and self.api_key[:8] != "sk-proj-":
            raise ValueError("openai api key must starts with 'sk-proj-'")


@dataclass
class LocalEmbeddingConfig:
    provider: Provider = "local"

    model_name: LocalEmbeddingModel = "examp"

    def __post_init__(self):
        if self.provider not in get_args(Provider):
            raise ValueError(f"Invalid provider: {self.provider}")

        if self.model_name not in get_args(LocalEmbeddingModel):
            raise ValueError(f"Invalid embedding model: {self.model_name}")
