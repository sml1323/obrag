"""
Ollama Embedding Implementation

로컬 Ollama 서버를 사용한 EmbeddingStrategy 구현체.
OpenAI 호환 API를 활용하여 구현.
"""

from typing import override

from openai import OpenAI

from .strategy import Vector


class OllamaEmbedder:
    """
    Ollama 임베딩 구현체.

    로컬 Ollama 서버를 통해 임베딩 생성.
    OpenAI 호환 API를 사용하므로 추가 의존성 없이 구현.
    """

    MODEL_DIMENSIONS: dict[str, int] = {
        "nomic-embed-text": 768,
        "mxbai-embed-large": 1024,
        "all-minilm": 384,
        "glm4:9b": 4096,
        "glm-4-9b": 4096,
    }

    def __init__(
        self,
        model_name: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434/v1",
    ):
        if not base_url.endswith("/v1"):
            base_url = f"{base_url.rstrip('/')}/v1"

        self.model_name: str = model_name
        self._base_url: str = base_url
        self._dimension: int = self.MODEL_DIMENSIONS.get(model_name, 768)
        self._client: OpenAI = OpenAI(
            base_url=base_url,
            api_key="ollama",
        )

    def embed(self, texts: list[str]) -> list[Vector]:
        if not texts:
            return []

        response = self._client.embeddings.create(
            model=self.model_name,
            input=texts,
        )

        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]

    def embed_query(self, query: str) -> Vector:
        return self.embed([query])[0]

    def embed_documents(self, documents: list[str]) -> list[Vector]:
        return self.embed(documents)

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def base_url(self) -> str:
        return self._base_url

    @override
    def __repr__(self) -> str:
        return f"OllamaEmbedder(model='{self.model_name}', dimension={self._dimension})"
