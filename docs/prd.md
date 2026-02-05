# [PRD] Obsidian AI: PARA 기반 지식 관리 및 프로젝트 대시보드

obsidian에 공부한 내용들을 정리하고 있거든? 하지만 기억은 잘 안나는데, 이걸 망각곡선에 따라서 rag, ai와 연계해서 복습하는 프로젝트를 만들어야 겠다.

## 1. 프로젝트 개요

- **목적:** 사용자의 옵시디언 노트를 AI가 학습하여 질문에 답하고, PARA 방법론에 기반한 프로젝트 진행률 및 복습 주기를 관리하는 통합 지식 관리 도구.
- **대상 사용자:** 옵시디언을 제2의 뇌로 활용하며, 지식의 유기적 연결과 체계적인 프로젝트 관리를 원하는 사용자.

## 2. 주요 기능 (Key Features)

### ① 지능형 RAG 채팅 (Semantic Search & Chat)

- **임베딩:** 옵시디언 `.md` 파일들을 벡터화하여 Vector DB에 저장.
- **멀티 모델 지원:** OpenAI, Gemini, Ollama(로컬) 중 선택 가능.
- **증분 업데이트:** 파일 수정/추가 시 전체를 다시 임베딩하지 않고, 변경된 파일만 식별하여 Vector DB를 업데이트 (File Hash 비교 방식 추천).

### ② PARA 프로젝트 대시보드

- **구조 분석:** `Project/` 폴더 하위의 디렉토리를 개별 프로젝트로 인식. ( 상위 폴더를 사용자가 직접 지정
- **진척도 관리:** 유저가 수동으로 입력한 달성률(%) 저장.
- **유기 프로젝트 식별:** 각 폴더 내 파일들의 `last_modified_date`를 추적하여 일정 기간(예: 2주) 수정이 없는 프로젝트를 '유기(Stale)' 상태로 표시.
- **시각화:** React와 Tailwind를 활용한 깔끔한 카드형/리스트형 대시보드.

### ③ 에빙하우스 복습 엔진 (Memory Boost)

- **방식 제안:** **태그(#review) 기반 관리**를 추천합니다. 폴더는 위치가 바뀔 수 있지만, 태그는 속성을 유지하기 때문입니다.
- **로직:** * 노트의 YAML 메타데이터에 `last_review_date`와 `review_count` 추가.
    - 에빙하우스 주기(1일, 3일, 7일, 14일, 30일)에 도달한 노트를 우선 노출.
    - 초기 단계에서는 '랜덤 복습' 버튼을 통해 전체 지식을 가볍게 훑기.

---

## 3. 기술 스택 (Tech Stack)

| **구분** | **기술** | **비고** |
| --- | --- | --- |
| **Language** | Python 3.10+ | FastAPI 또는 Flask (백엔드) |
| **Frontend** | React, Tailwind CSS | Vite 환경 추천 |
| **Vector DB** | **ChromaDB** | 로컬 저장이 쉽고 파이썬 라이브러리가 매우 강력함 |
| **Embedding** | BGE-M3 (Local) / text-embedding-3-small (Cloud) | LangChain 또는 LlamaIndex 활용 |
| **LLM Orchestration** | LangChain / LlamaIndex | Ollama 및 API 연동 용이 |
| **Deployment** | Docker, Docker-Compose | 컨테이너 기반 환경 구성 |
| **Desktop Tool** | Electron 또는 **Tauri** | 추후 Mac App 전환 시 Tauri 추천 (가벼움) |