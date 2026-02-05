"""
ChromaDB Vector Store

청크를 벡터화하여 저장하고 유사도 검색을 수행하는 모듈.
EmbeddingStrategy 패턴을 통해 임베더 교체 가능.
"""

import hashlib
import re
from pathlib import Path
from typing import List, Optional, Union

import chromadb

from core.embedding import EmbeddingStrategy, OpenAIEmbedder


# ============================================================================
# Collection Name Utilities
# ============================================================================


def sanitize_collection_name(name: str) -> str:
    """
    ChromaDB 컬렉션명 제약조건에 맞게 이름 정규화.

    ChromaDB 제약:
    - 3-63자
    - 시작/끝: 알파벳 또는 숫자
    - 중간: 알파벳, 숫자, _, -, .
    - 연속 .. 불가
    - IPv4 형식 불가
    """
    name = name.lower()
    name = name.replace("/", "_")
    name = re.sub(r"[^a-z0-9_\-.]", "_", name)
    while ".." in name:
        name = name.replace("..", ".")
    while "__" in name:
        name = name.replace("__", "_")
    name = name.strip("_-.")
    if len(name) < 3:
        name = name + "_col"
    if len(name) > 63:
        name = name[:63].rstrip("_-.")
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", name):
        name = "col_" + name
    return name


def derive_collection_name(base_name: str, model_name: str) -> str:
    """
    기본 컬렉션명과 모델명을 결합하여 고유 컬렉션명 생성.

    예: obsidian_notes + text-embedding-3-small -> obsidian_notes_text-embedding-3-small
    """
    combined = f"{base_name}_{model_name}"
    return sanitize_collection_name(combined)


# ============================================================================
# Custom Embedding Function Adapter
# ============================================================================


class _EmbeddingFunctionAdapter:
    """
    EmbeddingStrategy를 ChromaDB EmbeddingFunction 인터페이스로 변환.

    ChromaDB는 자체 EmbeddingFunction 인터페이스를 사용하므로,
    우리의 EmbeddingStrategy를 어댑터를 통해 연결.
    """

    def __init__(self, strategy: EmbeddingStrategy):
        self._strategy = strategy

    def __call__(self, input: List[str]) -> List[List[float]]:
        """ChromaDB가 문서 추가 시 호출하는 메서드"""
        return self._strategy.embed(input)

    def embed_query(self, input: List[str]) -> List[List[float]]:
        """ChromaDB가 쿼리 시 호출하는 메서드"""
        return self._strategy.embed(input)

    def name(self) -> str:
        """ChromaDB EmbeddingFunction 인터페이스 요구사항"""
        return f"custom_{type(self._strategy).__name__}"


# ============================================================================
# ChromaStore Class
# ============================================================================


class ChromaStore:
    """
    ChromaDB 기반 벡터 저장소.

    사용법:
        # 기본 (OpenAI 임베딩)
        store = ChromaStore()

        # Custom embedder
        from core.embedding import FakeEmbedder
        store = ChromaStore(embedder=FakeEmbedder())

        store.add_chunks(chunks)
        results = store.query("검색어", n_results=5)
    """

    def __init__(
        self,
        persist_path: str = "./chroma_db",
        collection_name: str = "obsidian_notes",
        embedder: Optional[EmbeddingStrategy] = None,
    ):
        """
        Args:
            persist_path: 데이터 저장 경로
            collection_name: 컬렉션 이름
            embedder: 임베딩 전략 (없으면 OpenAIEmbedder 사용)
        """
        self.persist_path = Path(persist_path).resolve()
        self.collection_name = collection_name

        # 임베더 설정 (기본: OpenAIEmbedder)
        self._embedder = embedder or OpenAIEmbedder()

        # ChromaDB용 어댑터 생성
        self._embedding_fn = _EmbeddingFunctionAdapter(self._embedder)

        # ChromaDB 클라이언트 및 컬렉션 생성
        self._client = chromadb.PersistentClient(path=str(self.persist_path))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embedding_fn,
        )

    @property
    def embedder(self) -> EmbeddingStrategy:
        """현재 사용 중인 임베더"""
        return self._embedder

    @staticmethod
    def _generate_chunk_id(chunk_text: str, source: str, index: int) -> str:
        """청크에 대한 고유 ID 생성"""
        content_hash = hashlib.md5(chunk_text.encode()).hexdigest()[:8]
        return f"{source}_{index}_{content_hash}"

    def add_chunks(self, chunks: List) -> int:
        """
        청크 리스트를 DB에 저장.

        Args:
            chunks: Chunk 객체 리스트

        Returns:
            저장된 청크 수
        """
        if not chunks:
            return 0

        documents = []
        metadatas = []
        ids = []

        for idx, chunk in enumerate(chunks):
            source = chunk.metadata.get("source", "unknown")
            chunk_id = self._generate_chunk_id(chunk.text, source, idx)

            documents.append(chunk.text)
            metadatas.append(chunk.metadata)
            ids.append(chunk_id)

        # ChromaDB에 추가 (임베딩은 자동으로 수행됨)
        self._collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        return len(documents)

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None,
    ) -> List[dict]:
        """
        텍스트 쿼리로 유사 청크 검색.

        Args:
            query_text: 검색 쿼리
            n_results: 반환할 결과 수
            where: 메타데이터 필터 (예: {"source": "note.md"})
            where_document: 문서 내용 필터 (예: {"$contains": "keyword"})

        Returns:
            검색 결과 리스트 [{"text": ..., "metadata": ..., "distance": ...}, ...]
        """
        query_params = {
            "query_texts": [query_text],
            "n_results": n_results,
        }

        if where:
            query_params["where"] = where
        if where_document:
            query_params["where_document"] = where_document

        results = self._collection.query(**query_params)

        # 결과 포맷팅
        formatted = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted.append(
                    {
                        "id": doc_id,
                        "text": results["documents"][0][i]
                        if results["documents"]
                        else None,
                        "metadata": results["metadatas"][0][i]
                        if results["metadatas"]
                        else {},
                        "distance": results["distances"][0][i]
                        if results["distances"]
                        else None,
                    }
                )

        return formatted

    def get_stats(self) -> dict:
        """
        컬렉션 통계 반환.

        Returns:
            {"name": ..., "count": ..., "embedder": ...}
        """
        return {
            "name": self.collection_name,
            "count": self._collection.count(),
            "persist_path": str(self.persist_path),
            "embedder": repr(self._embedder),
        }

    def clear(self) -> None:
        """컬렉션 내 모든 데이터 삭제"""
        # 컬렉션 삭제 후 재생성
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._embedding_fn,
        )

    def delete_by_source(self, source: str) -> None:
        """
        특정 source의 모든 청크 삭제.

        Args:
            source: 삭제할 파일명
        """
        self._collection.delete(where={"source": source})

    # ========================================================================
    # Incremental Sync Methods
    # ========================================================================

    @staticmethod
    def generate_deterministic_id(relative_path: str, chunk_index: int) -> str:
        """
        파일 경로 + 청크 인덱스 기반 deterministic ID 생성.

        증분 동기화에서 upsert가 정상 동작하도록 동일 파일의 동일 청크는
        항상 같은 ID를 가집니다.

        Args:
            relative_path: 루트 기준 상대 경로
            chunk_index: 청크 인덱스 (0부터 시작)

        Returns:
            "relative/path.md::chunk_0" 형태의 ID
        """
        return f"{relative_path}::chunk_{chunk_index}"

    def upsert_chunks(self, chunks: List, relative_path: str) -> int:
        """
        청크를 upsert (있으면 업데이트, 없으면 추가).

        증분 동기화용 메서드. deterministic ID를 사용하여
        동일 파일의 청크가 변경되어도 기존 청크를 덮어씁니다.

        Args:
            chunks: Chunk 객체 리스트
            relative_path: 루트 기준 상대 경로 (ID 생성에 사용)

        Returns:
            upsert된 청크 수
        """
        if not chunks:
            return 0

        documents = []
        metadatas = []
        ids = []

        for idx, chunk in enumerate(chunks):
            chunk_id = self.generate_deterministic_id(relative_path, idx)

            documents.append(chunk.text)
            # ChromaDB 호환 메타데이터로 변환
            metadatas.append(self._normalize_metadata(chunk.metadata))
            ids.append(chunk_id)

        # ChromaDB upsert (있으면 update, 없으면 insert)
        self._collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        return len(documents)

    @staticmethod
    def _normalize_metadata(metadata: dict) -> dict:
        """
        ChromaDB 호환 메타데이터로 변환.

        ChromaDB는 메타데이터 값으로 str, int, float, bool, None만 허용.
        리스트/딕셔너리는 JSON 문자열로 변환합니다.

        Args:
            metadata: 원본 메타데이터

        Returns:
            정규화된 메타데이터
        """
        import json

        normalized = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                normalized[key] = value
            elif isinstance(value, (list, dict)):
                # 리스트/딕셔너리는 JSON 문자열로 변환
                normalized[key] = json.dumps(value, ensure_ascii=False)
            else:
                # 기타 타입은 문자열로 변환
                normalized[key] = str(value)
        return normalized

    def delete_by_relative_path(self, relative_path: str) -> None:
        """
        특정 파일(relative_path)의 모든 청크 삭제.

        메타데이터의 relative_path 필드를 기준으로 삭제합니다.

        Args:
            relative_path: 삭제할 파일의 상대 경로
        """
        self._collection.delete(where={"relative_path": relative_path})

    def delete_chunks_by_prefix(self, relative_path: str, from_index: int) -> None:
        """
        특정 파일의 특정 인덱스 이상 청크 삭제.

        파일 수정 후 청크 수가 줄었을 때, 기존 초과 청크를 정리합니다.

        Args:
            relative_path: 파일 상대 경로
            from_index: 이 인덱스부터 삭제 (0-based)
        """
        # ID 패턴 기반으로 삭제할 청크 ID 목록 생성
        # ChromaDB에서 prefix 기반 삭제가 어려우므로, 개별 ID로 삭제
        ids_to_delete = []

        # 최대 1000개 청크까지 지원 (충분히 큰 수)
        for i in range(from_index, from_index + 1000):
            chunk_id = self.generate_deterministic_id(relative_path, i)
            ids_to_delete.append(chunk_id)

        # 존재하지 않는 ID는 ChromaDB가 무시함
        try:
            self._collection.delete(ids=ids_to_delete)
        except Exception:
            # 삭제할 ID가 없으면 무시
            pass

    def __repr__(self) -> str:
        return f"ChromaStore(collection='{self.collection_name}', count={self._collection.count()})"


# ============================================================================
# Convenience Functions
# ============================================================================


def create_store(
    persist_path: str = "./chroma_db",
    collection_name: str = "obsidian_notes",
    embedder: Optional[EmbeddingStrategy] = None,
) -> ChromaStore:
    """
    ChromaStore 인스턴스 생성 편의 함수.

    Args:
        persist_path: 데이터 저장 경로
        collection_name: 컬렉션 이름
        embedder: 임베딩 전략 (Optional)

    Returns:
        ChromaStore 인스턴스
    """
    return ChromaStore(
        persist_path=persist_path,
        collection_name=collection_name,
        embedder=embedder,
    )


def store_chunks(
    chunks: List,
    persist_path: str = "./chroma_db",
    collection_name: str = "obsidian_notes",
    embedder: Optional[EmbeddingStrategy] = None,
) -> int:
    """
    청크를 ChromaDB에 저장하는 편의 함수.

    Args:
        chunks: Chunk 리스트
        persist_path: 저장 경로
        collection_name: 컬렉션 이름
        embedder: 임베딩 전략 (Optional)

    Returns:
        저장된 청크 수
    """
    store = ChromaStore(
        persist_path=persist_path,
        collection_name=collection_name,
        embedder=embedder,
    )
    return store.add_chunks(chunks)


def search_chunks(
    query: str,
    n_results: int = 5,
    persist_path: str = "./chroma_db",
    collection_name: str = "obsidian_notes",
    embedder: Optional[EmbeddingStrategy] = None,
) -> List[dict]:
    """
    ChromaDB에서 유사 청크 검색하는 편의 함수.

    Args:
        query: 검색 쿼리
        n_results: 결과 수
        persist_path: 저장 경로
        collection_name: 컬렉션 이름
        embedder: 임베딩 전략 (Optional)

    Returns:
        검색 결과 리스트
    """
    store = ChromaStore(
        persist_path=persist_path,
        collection_name=collection_name,
        embedder=embedder,
    )
    return store.query(query, n_results=n_results)
