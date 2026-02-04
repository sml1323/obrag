"""
Chat Router 디버깅용 스크립트

API 엔드포인트를 거치지 않고 RAG 파이프라인 내부를 직접 탐색합니다.
VSCode/PyCharm에서 breakpoint 걸고 F5로 디버깅하세요.

사용법:
    python -m tasktests.phase2.debug_chat
    또는 IDE에서 이 파일을 디버그 실행
"""

import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv(project_root / ".env")

from core.rag import RAGChain, Retriever, PromptBuilder
from core.llm import LLMFactory
from core.embedding import EmbedderFactory
from db.chroma_store import ChromaStore
from config.models import OpenAILLMConfig, OpenAIEmbeddingConfig
import os


def main():
    print("=" * 60)
    print("🔍 Chat Router 디버깅 시작")
    print("=" * 60)

    # ========================================
    # 1. 의존성 직접 구성
    # ========================================
    print("\n📦 [1] 의존성 초기화")
    print("-" * 40)

    # Embedder
    embed_config = OpenAIEmbeddingConfig(
        model_name=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    )
    embedder = EmbedderFactory.create(embed_config)
    print(f"  Embedder: {embed_config.model_name}")

    # ChromaStore
    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    chroma_store = ChromaStore(
        persist_path=chroma_path,
        collection_name="obsidian_notes",
        embedder=embedder,
    )
    print(f"  ChromaDB: {chroma_path}")

    # LLM
    llm_config = OpenAILLMConfig(model_name=os.getenv("LLM_MODEL", "gpt-4o-mini"))
    llm = LLMFactory.create(llm_config)
    print(f"  LLM: {llm_config.model_name}")

    # Retriever + RAGChain
    retriever = Retriever(chroma_store)
    chain = RAGChain(retriever=retriever, llm=llm)
    print("  RAGChain: 초기화 완료")

    # ========================================
    # 2. 테스트 쿼리 설정
    # ========================================
    question = "Transformer 아키텍처에 대해 설명해줘"  # 👈 원하는 질문으로 변경
    top_k = 5
    temperature = 0.7

    print(f"\n❓ 질문: {question}")
    print(f"   top_k={top_k}, temperature={temperature}")

    # ========================================
    # 3. Step-by-Step 파이프라인 실행
    # ========================================

    # ---- Step 3.1: Retriever.retrieve() ----
    print("\n🔎 [3.1] Retriever.retrieve()")
    print("-" * 40)

    retrieval_result = retriever.retrieve(question, top_k=top_k)  # 👈 breakpoint!

    print(f"  검색된 청크 수: {retrieval_result.total_count}")
    for i, chunk in enumerate(retrieval_result.chunks):
        print(f"\n  === Chunk {i + 1} ===")
        print(f"  📍 Source: {chunk.metadata.get('source', 'unknown')}")
        print(f"  📊 Score: {chunk.score:.4f} (distance: {chunk.distance:.4f})")
        print(f"  🏷️ Headers: {chunk.metadata.get('headers', [])}")
        preview = chunk.text[:150].replace("\n", " ")
        print(f"  📝 Preview: {preview}...")

    # ---- Step 3.2: retrieve_with_context() ----
    print("\n📄 [3.2] retrieve_with_context()")
    print("-" * 40)

    context = retriever.retrieve_with_context(question, top_k=top_k)  # 👈 breakpoint!

    print(f"  Context 길이: {len(context)} 문자")
    print(f"  Context 미리보기:\n{context[:500]}...")

    # ---- Step 3.3: PromptBuilder.build() ----
    print("\n✍️ [3.3] PromptBuilder.build()")
    print("-" * 40)

    prompt_builder = chain.prompt_builder
    messages = prompt_builder.build(
        question=question, context=context
    )  # 👈 breakpoint!

    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        print(f"\n  [{role.upper()}]")
        if len(content) > 300:
            print(f"  {content[:300]}...")
            print(f"  ... (총 {len(content)} 문자)")
        else:
            print(f"  {content}")

    # ---- Step 3.4: LLM.generate() (비용 주의!) ----
    print("\n🤖 [3.4] LLM.generate()")
    print("-" * 40)

    # ⚠️ 실제 API 호출됨 - 비용 발생!
    # 디버깅만 할 때는 이 부분 주석처리 권장

    CALL_LLM = True  # False로 변경하면 LLM 호출 스킵

    if CALL_LLM:
        llm_response = llm.generate(messages, temperature=temperature)  # 👈 breakpoint!

        print(f"  Model: {llm_response.model}")
        print(f"  Usage: {llm_response.usage}")
        print(f"\n  📝 Response:")
        print(f"  {llm_response.content[:500]}...")
    else:
        print("  ⏭️ LLM 호출 스킵됨 (CALL_LLM=False)")

    # ========================================
    # 4. RAGChain.query() - 전체 파이프라인
    # ========================================
    print("\n🚀 [4] RAGChain.query() - 전체 파이프라인")
    print("-" * 40)

    if CALL_LLM:
        response = chain.query(
            question,
            top_k=top_k,
            temperature=temperature,
        )  # 👈 breakpoint!

        print(f"  Model: {response.model}")
        print(f"  Usage: {response.usage}")
        print(f"  Sources: {len(response.retrieval_result.chunks)}개")
        print(f"\n  📝 Answer:")
        print(f"  {response.answer}")
    else:
        print("  ⏭️ 전체 파이프라인 스킵됨 (CALL_LLM=False)")

    # ========================================
    # 5. 멀티턴 대화 (선택)
    # ========================================
    print("\n💬 [5] query_with_history() - 멀티턴")
    print("-" * 40)

    if CALL_LLM:
        history = [
            {"role": "user", "content": "RAG가 뭐야?"},
            {
                "role": "assistant",
                "content": "RAG는 Retrieval-Augmented Generation의 약자로...",
            },
        ]

        followup = "그럼 임베딩은 어떻게 동작해?"

        response2 = chain.query_with_history(
            followup,
            history=history,
            top_k=3,
        )  # 👈 breakpoint!

        print(f"  Follow-up 질문: {followup}")
        print(f"\n  📝 Answer:")
        print(f"  {response2.answer[:500]}...")
    else:
        print("  ⏭️ 멀티턴 스킵됨 (CALL_LLM=False)")

    print("\n" + "=" * 60)
    print("✅ 디버깅 완료!")
    print("=" * 60)


def debug_dynamic_chain():
    """
    _get_dynamic_chain() 로직 디버깅.

    chat.py의 동적 체인 생성 로직을 분리해서 테스트합니다.
    """
    print("\n🔧 동적 체인 생성 디버깅")
    print("=" * 60)

    from config.models import GeminiLLMConfig, OllamaLLMConfig

    # 다양한 provider 테스트
    providers = [
        ("openai", "gpt-4o-mini", os.getenv("OPENAI_API_KEY")),
        ("gemini", "gemini-1.5-flash", os.getenv("GOOGLE_API_KEY")),
        # ("ollama", "llama3", None),  # 로컬 Ollama 필요
    ]

    for provider, model, api_key in providers:
        print(f"\n  Testing: {provider}/{model}")
        try:
            if provider == "openai":
                config = OpenAILLMConfig(model_name=model, api_key=api_key)
            elif provider == "gemini":
                config = GeminiLLMConfig(model_name=model, api_key=api_key)
            elif provider == "ollama":
                config = OllamaLLMConfig(model_name=model)

            llm = LLMFactory.create(config)  # 👈 breakpoint!
            print(f"    ✅ LLM 생성 성공: {llm.model_name}")
        except Exception as e:
            print(f"    ❌ 실패: {e}")


if __name__ == "__main__":
    main()

    # 동적 체인 디버깅도 필요하면 주석 해제
    # debug_dynamic_chain()
