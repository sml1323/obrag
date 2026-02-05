from dataclasses import dataclass
from typing import Literal, Union, get_args

Provider = Literal["local", "openai", "ollama", "sentence_transformers"]
OpenAIEmbeddingModel = Literal["text-embedding-3-small", "text-embedding-3-large"]
LocalEmbeddingModel = Literal["bge-m3", "bge-large-zh", "bge-base-en"]
OllamaEmbeddingModel = Literal["nomic-embed-text", "mxbai-embed-large", "all-minilm"]
SentenceTransformerModel = Literal["BAAI/bge-m3", "dragonkue/BGE-m3-ko"]


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

    model_name: LocalEmbeddingModel = "bge-m3"

    def __post_init__(self):
        if self.provider not in get_args(Provider):
            raise ValueError(f"Invalid provider: {self.provider}")

        if self.model_name not in get_args(LocalEmbeddingModel):
            raise ValueError(f"Invalid embedding model: {self.model_name}")


@dataclass
class OllamaEmbeddingConfig:
    """Ollama 임베딩 설정"""

    provider: Provider = "ollama"
    model_name: str = "nomic-embed-text"
    base_url: str = "http://localhost:11434"

    def __post_init__(self):
        if self.provider not in get_args(Provider):
            raise ValueError(f"Invalid provider: {self.provider}")
        # Allow any string for model_name to support custom models


@dataclass
class SentenceTransformerEmbeddingConfig:
    """SentenceTransformer 임베딩 설정"""

    provider: Provider = "sentence_transformers"
    model_name: str = "BAAI/bge-m3"

    def __post_init__(self):
        if self.provider not in get_args(Provider):
            raise ValueError(f"Invalid provider: {self.provider}")


# Union type for factory pattern
EmbeddingConfig = Union[
    OpenAIEmbeddingConfig,
    LocalEmbeddingConfig,
    OllamaEmbeddingConfig,
    SentenceTransformerEmbeddingConfig,
]


# ============================================================================
# LLM Config Types
# ============================================================================

LLMProvider = Literal["openai", "gemini", "ollama"]
OpenAILLMModel = Literal["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
GeminiLLMModel = Literal["gemini-1.5-pro", "gemini-1.5-flash"]


@dataclass
class OpenAILLMConfig:
    """OpenAI LLM 설정"""

    provider: LLMProvider = "openai"
    model_name: OpenAILLMModel = "gpt-4o-mini"
    api_key: str | None = None

    def __post_init__(self):
        if self.model_name not in get_args(OpenAILLMModel):
            raise ValueError(f"Invalid OpenAI LLM model: {self.model_name}")
        if self.api_key is not None and not self.api_key.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")


@dataclass
class GeminiLLMConfig:
    """Gemini LLM 설정"""

    provider: LLMProvider = "gemini"
    model_name: GeminiLLMModel = "gemini-1.5-flash"
    api_key: str | None = None

    def __post_init__(self):
        if self.model_name not in get_args(GeminiLLMModel):
            raise ValueError(f"Invalid Gemini LLM model: {self.model_name}")


@dataclass
class OllamaLLMConfig:
    """Ollama LLM 설정"""

    provider: LLMProvider = "ollama"
    model_name: str = "llama3"
    base_url: str = "http://localhost:11434"


# Union type for LLM factory pattern
LLMConfig = Union[OpenAILLMConfig, GeminiLLMConfig, OllamaLLMConfig]
