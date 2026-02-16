"""
Embedding Strategy Pattern

임베딩 전략을 위한 Protocol 및 구현체.
의존성 주입을 통해 테스트 용이성과 임베더 교체 유연성 확보.
"""

from typing import List, Protocol


# ============================================================================
# Type Aliases
# ============================================================================

Vector = List[float]


# ============================================================================
# Protocol Definition
# ============================================================================


class EmbeddingStrategy(Protocol):
    """
    임베딩 전략 Protocol.

    모든 임베더는 이 프로토콜을 구현해야 합니다.
    """

    def embed(self, texts: List[str]) -> List[Vector]:
        """
        텍스트 리스트를 벡터 리스트로 변환.

        Args:
            texts: 임베딩할 텍스트 리스트

        Returns:
            각 텍스트에 대한 임베딩 벡터 리스트
        """
        ...

    def embed_query(self, query: str) -> Vector:
        """
        쿼리 전용 임베딩.

        instruction-tuned 모델(E5 등)은 쿼리에 다른 prefix 사용.
        기본 구현은 embed()를 호출.
        """
        ...

    def embed_documents(self, documents: List[str]) -> List[Vector]:
        """
        문서 전용 임베딩.

        instruction-tuned 모델(E5 등)은 문서에 다른 prefix 사용.
        기본 구현은 embed()를 호출.
        """
        ...

    @property
    def dimension(self) -> int:
        """임베딩 벡터 차원"""
        ...

    @property
    def model_name(self) -> str:
        """사용 중인 모델 이름"""
        ...


# ============================================================================
# Fake Embedder (Testing)
# ============================================================================


class FakeEmbedder:
    """
    테스트용 가짜 임베더.

    텍스트 길이를 기반으로 간단한 벡터 생성.
    단위 테스트에서 실제 API 호출 없이 빠르게 테스트 가능.
    """

    def __init__(self, dimension: int = 8, model_name: str = "fake-embedder"):
        self._dimension = dimension
        self._model_name = model_name

    def embed(self, texts: List[str]) -> List[Vector]:
        """텍스트 길이 기반 가짜 임베딩 생성"""
        vectors = []
        for text in texts:
            base = float(len(text))
            text_hash = hash(text) % 1000
            vector = [(base + i + text_hash) / 1000.0 for i in range(self._dimension)]
            vectors.append(vector)
        return vectors

    def embed_query(self, query: str) -> Vector:
        return self.embed([query])[0]

    def embed_documents(self, documents: List[str]) -> List[Vector]:
        return self.embed(documents)

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name
