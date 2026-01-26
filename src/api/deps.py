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
from db.chroma_store import ChromaStore
from config.models import OpenAILLMConfig, OpenAIEmbeddingConfig


# ============================================================================
# App State
# ============================================================================

@dataclass
class AppState:
    """앱 전역 상태 (Lifespan에서 초기화)."""

    chroma_store: ChromaStore
    rag_chain: RAGChain


def init_app_state(
    chroma_path: str = "./chroma_db",
    collection_name: str = "obsidian_notes",
) -> AppState:
    """
    앱 상태 초기화.

    환경변수에서 설정을 읽고 필요한 객체들을 생성합니다.

    Args:
        chroma_path: ChromaDB 저장 경로
        collection_name: 컬렉션 이름

    Returns:
        초기화된 AppState
    """
    # 1. Embedder 생성
    embed_config = OpenAIEmbeddingConfig(
        model_name=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    )
    embedder = EmbedderFactory.create(embed_config)

    # 2. ChromaStore 생성
    chroma_store = ChromaStore(
        persist_path=chroma_path,
        collection_name=collection_name,
        embedder=embedder,
    )

    # 3. LLM 생성
    llm_config = OpenAILLMConfig(
        model_name=os.getenv("LLM_MODEL", "gpt-4o-mini")
    )
    llm = LLMFactory.create(llm_config)

    # 4. Retriever + RAGChain 생성
    retriever = Retriever(chroma_store)
    rag_chain = RAGChain(retriever=retriever, llm=llm)

    return AppState(
        chroma_store=chroma_store,
        rag_chain=rag_chain,
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
