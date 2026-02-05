"""
Dependency Injection Module

FastAPI 엔드포인트에 주입할 의존성을 정의합니다.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import os

from dotenv import load_dotenv

# .env 파일 로드 (src/.env)
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

from fastapi import Request
from core.rag import RAGChain, Retriever
from core.llm import LLMFactory
from core.embedding import EmbedderFactory
from core.sync.incremental_syncer import IncrementalSyncer, create_syncer
from db.chroma_store import ChromaStore, derive_collection_name
from config.models import OpenAILLMConfig, OpenAIEmbeddingConfig
from sqlmodel import Session
from db.engine import engine


# ============================================================================
# App State
# ============================================================================


@dataclass
class AppState:
    """앱 전역 상태 (Lifespan에서 초기화)."""

    chroma_store: ChromaStore
    rag_chain: RAGChain
    syncer: IncrementalSyncer


def init_app_state(
    chroma_path: str = "./chroma_db",
    base_collection_name: str = "obsidian_notes",
    auto_derive_collection: bool = True,
) -> AppState:
    """
    앱 상태 초기화.

    환경변수에서 설정을 읽고 필요한 객체들을 생성합니다.

    Args:
        chroma_path: ChromaDB 저장 경로
        base_collection_name: 기본 컬렉션 이름
        auto_derive_collection: True면 임베딩 모델명을 컬렉션명에 포함

    Returns:
        초기화된 AppState
    """
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
    embedding_model = os.getenv("EMBEDDING_MODEL", "")

    if embedding_provider == "ollama":
        from config.models import OllamaEmbeddingConfig

        if not embedding_model:
            embedding_model = "nomic-embed-text"
        embed_config = OllamaEmbeddingConfig(
            model_name=embedding_model,  # type: ignore
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    elif embedding_provider == "sentence_transformers":
        from config.models import SentenceTransformerEmbeddingConfig

        if not embedding_model:
            embedding_model = "BAAI/bge-m3"
        embed_config = SentenceTransformerEmbeddingConfig(
            model_name=embedding_model,
        )
    else:
        if not embedding_model:
            embedding_model = "text-embedding-3-small"
        embed_config = OpenAIEmbeddingConfig(
            model_name=embedding_model  # type: ignore
        )

    embedder = EmbedderFactory.create(embed_config)

    if auto_derive_collection:
        collection_name = derive_collection_name(
            base_collection_name, embedder.model_name
        )
    else:
        collection_name = base_collection_name

    chroma_store = ChromaStore(
        persist_path=chroma_path,
        collection_name=collection_name,
        embedder=embedder,
    )

    llm_config = OpenAILLMConfig(model_name=os.getenv("LLM_MODEL", "gpt-4o-mini"))  # type: ignore
    llm = LLMFactory.create(llm_config)

    retriever = Retriever(chroma_store)
    rag_chain = RAGChain(retriever=retriever, llm=llm)

    obsidian_path = os.getenv("OBSIDIAN_PATH", "./docs")
    syncer = create_syncer(root_path=obsidian_path, chroma_store=chroma_store)

    return AppState(
        chroma_store=chroma_store,
        rag_chain=rag_chain,
        syncer=syncer,
    )


# ============================================================================
# Dependency Functions
# ============================================================================


def get_app_state(request: Request) -> AppState:
    """요청에서 앱 상태 가져오기."""
    return request.app.state.deps


def get_rag_chain(request: Request) -> RAGChain:
    """RAGChain 의존성 주입."""
    return request.app.state.deps.rag_chain


def get_chroma_store(request: Request) -> ChromaStore:
    """ChromaStore 의존성 주입."""
    return request.app.state.deps.chroma_store


def get_syncer(request: Request) -> IncrementalSyncer:
    """IncrementalSyncer 의존성 주입."""
    return request.app.state.deps.syncer


def get_session():
    """DB Session 의존성 주입."""
    with Session(engine) as session:
        yield session
