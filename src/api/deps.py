"""
Dependency Injection Module

FastAPI 엔드포인트에 주입할 의존성을 정의합니다.
"""

from dataclasses import dataclass
from typing import Optional, Generator
from pathlib import Path
from threading import Lock
import os

from dotenv import load_dotenv

# .env 파일 로드 (src/.env)
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

from fastapi import Request, Depends, HTTPException
from core.rag import RAGChain, Retriever
from core.llm import LLMFactory
from core.embedding import EmbedderFactory
from core.sync.incremental_syncer import IncrementalSyncer, create_syncer
from db.chroma_store import ChromaStore, derive_collection_name
from config.models import (
    OpenAILLMConfig,
    GeminiLLMConfig,
    OpenAIEmbeddingConfig,
    OllamaEmbeddingConfig,
    OllamaLLMConfig,
    SentenceTransformerEmbeddingConfig,
    MultilingualE5EmbeddingConfig,
    LocalEmbeddingConfig,
)
from sqlmodel import Session
from db.engine import engine
from core.domain.settings import Settings


# ============================================================================
# Resource Cache  (embedder / store / llm 를 설정 시그니처별로 1회만 생성)
#
# get_rag_chain 등은 요청마다 호출되므로, 무거운 리소스(특히 수 GB SentenceTransformer
# 모델과 ChromaDB PersistentClient)를 매 요청 재생성하면 지연·메모리 churn 이 폭발한다.
# 아래 캐시는 (provider, model, api_key, base_url) 시그니처가 같으면 동일 인스턴스를
# 재사용하여, 로딩된 모델 가중치를 프로세스 수명 동안 유지한다.
# ============================================================================

_embedder_cache: dict = {}
_store_cache: dict = {}
_llm_cache: dict = {}
_cache_lock = Lock()


def _build_embedding_config(
    provider: str | None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
):
    """provider 문자열을 적절한 EmbeddingConfig 로 변환 (모든 provider 분기 포함)."""
    provider = (provider or "openai").lower()
    if provider == "ollama":
        return OllamaEmbeddingConfig(
            model_name=model or "nomic-embed-text",
            base_url=base_url or "http://localhost:11434",
        )
    elif provider == "sentence_transformers":
        return SentenceTransformerEmbeddingConfig(model_name=model or "BAAI/bge-m3")
    elif provider == "multilingual_e5":
        return MultilingualE5EmbeddingConfig(
            model_name=model or "intfloat/multilingual-e5-large-instruct"
        )
    elif provider == "local":
        return LocalEmbeddingConfig(model_name=model or "bge-m3")  # type: ignore
    else:
        return OpenAIEmbeddingConfig(
            model_name=model or "text-embedding-3-small",  # type: ignore
            api_key=api_key,
        )


def _build_llm_config(
    provider: str | None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
):
    """provider 문자열을 적절한 LLMConfig 로 변환."""
    provider = (provider or "openai").lower()
    if provider == "ollama":
        return OllamaLLMConfig(
            model_name=model or "llama3",
            base_url=base_url or "http://localhost:11434",
        )
    elif provider == "gemini":
        return GeminiLLMConfig(
            model_name=model or "gemini-1.5-flash",  # type: ignore
            api_key=api_key,
        )
    else:
        return OpenAILLMConfig(
            model_name=model or "gpt-4o-mini",  # type: ignore
            api_key=api_key,
        )


def build_embedder(
    provider: str | None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
):
    """
    캐시된 Embedder 반환. 동일 설정이면 같은 인스턴스를 재사용한다.

    Returns:
        (embedder, model_name) 튜플
    """
    config = _build_embedding_config(provider, model, api_key, base_url)
    key = (
        config.provider,
        config.model_name,
        getattr(config, "api_key", None),
        getattr(config, "base_url", None),
    )
    with _cache_lock:
        embedder = _embedder_cache.get(key)
        if embedder is None:
            embedder = EmbedderFactory.create(config)
            _embedder_cache[key] = embedder
    return embedder, config.model_name


def build_store(
    persist_path: str,
    base_collection_name: str,
    embedder,
    model_name: str,
) -> ChromaStore:
    """캐시된 ChromaStore 반환 (resolved path + collection 단위)."""
    collection_name = derive_collection_name(base_collection_name, model_name)
    key = (str(Path(persist_path).resolve()), collection_name)
    with _cache_lock:
        store = _store_cache.get(key)
        if store is None:
            store = ChromaStore(
                persist_path=persist_path,
                collection_name=collection_name,
                embedder=embedder,
            )
            _store_cache[key] = store
    return store


def build_llm(
    provider: str | None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
):
    """캐시된 LLM 클라이언트 반환."""
    config = _build_llm_config(provider, model, api_key, base_url)
    key = (
        config.provider,
        config.model_name,
        getattr(config, "api_key", None),
        getattr(config, "base_url", None),
    )
    with _cache_lock:
        llm = _llm_cache.get(key)
        if llm is None:
            llm = LLMFactory.create(config)
            _llm_cache[key] = llm
    return llm


def reset_resource_caches() -> None:
    """embedder/store/llm 캐시를 비운다 (주로 테스트 격리용)."""
    with _cache_lock:
        _embedder_cache.clear()
        _store_cache.clear()
        _llm_cache.clear()


# ============================================================================
# App State
# ============================================================================


@dataclass
class AppState:
    """앱 전역 상태 (Lifespan에서 초기화)."""

    chroma_store: ChromaStore
    rag_chain: RAGChain
    syncer: Optional[IncrementalSyncer]


def init_app_state(
    chroma_path: str | None = None,
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
    # Default embedder: sentence_transformers (no API key required)
    # Actual embedder is dynamically created from DB Settings in get_rag_chain
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    embedder, embed_model_name = build_embedder(
        provider=os.getenv("EMBEDDING_PROVIDER", "sentence_transformers"),
        model=os.getenv("EMBEDDING_MODEL") or None,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=ollama_base_url,
    )

    if chroma_path is None:
        chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")

    if auto_derive_collection:
        chroma_store = build_store(
            chroma_path, base_collection_name, embedder, embed_model_name
        )
    else:
        key = (str(Path(chroma_path).resolve()), base_collection_name)
        with _cache_lock:
            chroma_store = _store_cache.get(key)
            if chroma_store is None:
                chroma_store = ChromaStore(
                    persist_path=chroma_path,
                    collection_name=base_collection_name,
                    embedder=embedder,
                )
                _store_cache[key] = chroma_store

    # Default LLM: Ollama (no API key required) for startup fallback
    # Actual LLM is dynamically created from DB Settings in get_rag_chain
    llm = build_llm(
        provider="ollama",
        model=os.getenv("LLM_MODEL", "llama3"),
        base_url=ollama_base_url,
    )

    retriever = Retriever(chroma_store)
    rag_chain = RAGChain(retriever=retriever, llm=llm)

    obsidian_path = os.getenv("VAULT_PATH", os.getenv("OBSIDIAN_PATH", "./docs"))
    syncer = None
    try:
        syncer = create_syncer(root_path=obsidian_path, chroma_store=chroma_store)
    except (FileNotFoundError, NotADirectoryError):
        print(
            f"[init] Vault path not found: {obsidian_path} — syncer disabled until configured via Settings."
        )

    return AppState(
        chroma_store=chroma_store,
        rag_chain=rag_chain,
        syncer=syncer,
    )


# ============================================================================
# Dependency Functions
# ============================================================================


def _create_embedder_from_settings(settings: Settings):
    """
    Settings에서 임베딩 설정을 읽어 (캐시된) Embedder 생성.

    Returns:
        (embedder, model_name) 튜플
    """
    return build_embedder(
        provider=settings.embedding_provider,
        model=settings.embedding_model or None,
        api_key=settings.embedding_api_key or settings.llm_api_key,
        base_url=settings.ollama_endpoint,
    )


def _create_llm_from_settings(settings: Settings):
    """Settings에서 LLM 설정을 읽어 (캐시된) LLM 생성."""
    return build_llm(
        provider=settings.llm_provider,
        model=settings.llm_model or None,
        api_key=settings.llm_api_key,
        base_url=settings.ollama_endpoint,
    )


def get_app_state(request: Request) -> AppState:
    """요청에서 앱 상태 가져오기."""
    return request.app.state.deps


def get_rag_chain(request: Request) -> RAGChain:
    """RAGChain 의존성 주입 - DB Settings 기반으로 동적 생성."""
    default_chain = request.app.state.deps.rag_chain
    default_store = request.app.state.deps.chroma_store

    with Session(engine) as db:
        db_settings = db.get(Settings, 1)
        if not db_settings:
            return default_chain

        try:
            embedder, model_name = _create_embedder_from_settings(db_settings)
            chroma_store = build_store(
                str(default_store.persist_path),
                "obsidian_notes",
                embedder,
                model_name,
            )

            llm = _create_llm_from_settings(db_settings)
            retriever = Retriever(chroma_store)
            return RAGChain(retriever=retriever, llm=llm)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            print(f"Failed to create dynamic RAGChain: {e}")
            return default_chain


def get_chroma_store(request: Request) -> ChromaStore:
    """ChromaStore 의존성 주입."""
    return request.app.state.deps.chroma_store


def get_syncer(request: Request) -> IncrementalSyncer:
    """IncrementalSyncer 의존성 주입."""
    syncer = request.app.state.deps.syncer
    if syncer is None:
        raise HTTPException(
            status_code=400,
            detail="No vault path configured. Please set vault_path in Settings first.",
        )
    return syncer


def get_session():
    """DB Session 의존성 주입."""
    with Session(engine) as session:
        yield session
