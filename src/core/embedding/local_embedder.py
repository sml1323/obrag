"""
Local Embedding Implementation (Skeleton)

BGE-M3 등 로컬 임베딩 모델을 위한 뼈대 구현.
실제 모델 로딩은 추후 구현 예정.
"""

from typing import List

from .strategy import Vector


# ============================================================================
# Local Embedder (Skeleton)
# ============================================================================

class LocalEmbedder:
    """
    로컬 임베딩 모델 구현체 (Skeleton).
    
    현재는 placeholder로, 실제 모델 로딩은 미구현 상태입니다.
    BGE-M3 또는 다른 로컬 모델 통합 시 이 클래스를 확장합니다.
    
    사용법:
        embedder = LocalEmbedder(model_name="bge-m3")
        # 현재는 NotImplementedError 발생
    """
    
    # 모델별 차원 수 (예상)
    MODEL_DIMENSIONS = {
        "bge-m3": 1024,
        "bge-large-zh": 1024,
        "bge-base-en": 768,
    }
    
    def __init__(self, model_name: str = "bge-m3"):
        """
        Args:
            model_name: 로컬 임베딩 모델 이름
        """
        self.model_name = model_name
        self._dimension = self.MODEL_DIMENSIONS.get(model_name, 1024)
        self._model = None  # TODO: 실제 모델 로딩
    
    def embed(self, texts: List[str]) -> List[Vector]:
        """
        텍스트 리스트를 벡터 리스트로 변환.
        
        현재 미구현 상태 - NotImplementedError 발생.
        
        Args:
            texts: 임베딩할 텍스트 리스트
        
        Returns:
            각 텍스트에 대한 임베딩 벡터 리스트
        
        Raises:
            NotImplementedError: 실제 모델 로딩 전까지 발생
        """
        raise NotImplementedError(
            f"LocalEmbedder({self.model_name}) is not yet implemented. "
            "Please use OpenAIEmbedder or wait for local model integration."
        )
    
    @property
    def dimension(self) -> int:
        """임베딩 벡터 차원"""
        return self._dimension
    
    def __repr__(self) -> str:
        return f"LocalEmbedder(model='{self.model_name}', dimension={self._dimension}, implemented=False)"
