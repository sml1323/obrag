"""
OpenAI Embedding Implementation

OpenAI text-embedding-3-small/large 모델을 사용한 임베딩 구현.
"""

import os
from typing import List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from .strategy import EmbeddingStrategy, Vector

# .env 파일 로드
from pathlib import Path
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)


# ============================================================================
# OpenAI Embedder
# ============================================================================

class OpenAIEmbedder:
    """
    OpenAI 임베딩 구현체.
    
    사용법:
        embedder = OpenAIEmbedder()
        vectors = embedder.embed(["Hello", "World"])
    """
    
    # 모델별 차원 수
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    
    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
    ):
        """
        Args:
            model_name: OpenAI 임베딩 모델 이름
            api_key: OpenAI API 키 (없으면 환경변수에서 로드)
        """
        self.model_name = model_name
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self._api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self._client = OpenAI(api_key=self._api_key)
        self._dimension = self.MODEL_DIMENSIONS.get(model_name, 1536)
    
    def embed(self, texts: List[str]) -> List[Vector]:
        """
        OpenAI API를 사용하여 텍스트 임베딩.
        
        Args:
            texts: 임베딩할 텍스트 리스트
        
        Returns:
            임베딩 벡터 리스트
        """
        if not texts:
            return []
        
        response = self._client.embeddings.create(
            model=self.model_name,
            input=texts,
        )
        
        # 결과를 입력 순서대로 정렬하여 반환
        embeddings = [None] * len(texts)
        for item in response.data:
            embeddings[item.index] = item.embedding
        
        return embeddings
    
    @property
    def dimension(self) -> int:
        """임베딩 벡터 차원"""
        return self._dimension
    
    def __repr__(self) -> str:
        return f"OpenAIEmbedder(model='{self.model_name}', dimension={self._dimension})"
