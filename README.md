<div align="center">

# Obsidian RAG

### 개인 지식 관리 AI 풀스택 시스템

Obsidian Vault의 마크다운 노트를 벡터화하여,
의미 기반 검색과 AI 채팅을 제공하는 RAG 애플리케이션

<br/>

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=for-the-badge&logo=next.js&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-FF6F00?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

<br/>

<video src="https://github.com/user-attachments/assets/15c993da-600b-4da0-ba38-da105f6b11c7" controls loop muted width="100%"></video>

</div>

---

## 왜 만들었나

Obsidian에 학습 내용을 정리하고 있지만, 노트가 수백 개로 늘어나면서 "분명 정리해둔 건데 어디 있는지 모르겠다"는 문제가 반복되었습니다. 키워드 검색으로는 한계가 있고, 문서의 맥락과 의미를 이해하는 검색이 필요했습니다.

직접 사용하는 도구를 직접 만들어보자는 동기로 시작한 프로젝트입니다.

---

## 시스템 아키텍처

### RAG 파이프라인

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│  Obsidian   │     │  Markdown    │     │   Semantic   │     │  ChromaDB   │
│  Vault (.md)│────▶│  Preprocessor│────▶│   Chunking   │────▶│  (Vector DB)│
└─────────────┘     └──────────────┘     └──────────────┘     └──────┬──────┘
                                                                     │
┌─────────────┐     ┌──────────────┐     ┌──────────────┐           │
│   LLM       │     │   Prompt     │     │  Retriever   │◀──────────┘
│   Response  │◀────│   Builder    │◀────│  (Top-k)     │
└─────────────┘     └──────────────┘     └──────────────┘
```

### 전체 시스템 구조

```
┌────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 16)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ RAG Chat │ │  PARA    │ │Embedding │ │   Settings   │  │
│  │          │ │Dashboard │ │  Status  │ │              │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘  │
│       └─────────────┴────────────┴──────────────┘          │
│                         REST API                           │
├────────────────────────────────────────────────────────────┤
│                    Backend (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    API Layer                          │  │
│  │  /chat  /sync  /topics  /sessions  /projects  ...    │  │
│  └──────────────────────┬───────────────────────────────┘  │
│  ┌──────────────────────┴───────────────────────────────┐  │
│  │                   Core Layer                          │  │
│  │  ┌─────────┐ ┌───────────┐ ┌────────┐ ┌──────────┐  │  │
│  │  │RAGChain │ │ LLM       │ │Embedder│ │Sync      │  │  │
│  │  │         │ │ Strategy  │ │Strategy│ │Engine    │  │  │
│  │  └─────────┘ └───────────┘ └────────┘ └──────────┘  │  │
│  └──────────────────────┬───────────────────────────────┘  │
│  ┌──────────────────────┴───────────────────────────────┐  │
│  │                   Data Layer                          │  │
│  │         ChromaDB (Vectors)  +  SQLite (Metadata)      │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

---

## 핵심 기술 결정

| 결정 | 선택 | 이유 |
|------|------|------|
| Vector DB | ChromaDB | 로컬 SQLite 기반으로 별도 서버 불필요, Docker 패키징 용이 |
| 검색 전략 | Hybrid (Vector + BM25) | 한국어 노트에서 의미 검색만으로는 부족, 키워드 매칭 병행 필요 |
| LLM 인터페이스 | Python Protocol (구조적 서브타이핑) | 모델 교체 시 코드 수정 최소화, 테스트 시 FakeLLM 주입 가능 |
| 청킹 전략 | 헤더 기반 Semantic Chunking | 마크다운 문서 구조(H1-H6) 보존, Breadcrumb 경로로 위치 컨텍스트 유지 |
| 동기화 | File Hash 기반 증분 동기화 | 수백 개 노트 전체 재처리는 비효율, 변경분만 감지하여 upsert |
| 메타데이터 DB | SQLite + SQLModel | 채팅 세션/토픽 관리에 경량 ORM 필요, ChromaDB와 역할 분리 |

---

## 개발 방법론: AI-Assisted SDD

이 프로젝트는 **AI 코딩 도구를 전면 활용한 설계 주도 개발(SDD) 실험**입니다.

Python만 다룰 수 있는 상태에서, AI 도구를 활용하여 프론트엔드(Next.js)부터 백엔드(FastAPI)까지 풀스택 시스템을 구축하는 실험을 진행했습니다.

**워크플로우:** `Make Plan` → `Create Task` → `Implement` → `Verify`

각 단계에서 AI에게 구현을 위임하되, 설계와 검증은 직접 수행하는 SDD(설계 주도 개발) 방식을 적용했습니다.

**사용 도구:** Claude Code, oh-my-opencode, antigravity, Vercel AI 등 다양한 AI 코딩 도구를 비교 실험

> 워크플로우 상세: [AI-Assisted SDD 워크플로우 문서](docs/sdd-workflow.md)

**얻은 인사이트:**

- **기술 부채 체감**: AI가 생성한 코드를 이해하지 못한 채 병합하면, 작은 오류가 쌓여 디버깅이 불가능한 상태가 됨
- **코드 이해의 중요성**: Neovim 환경에서 Python 디버거(pdb)로 변수 흐름을 직접 추적하며 코드를 이해하는 과정을 거침
- **워크플로우 진화**: 이 경험을 바탕으로 이후 프로젝트([Coin Anomaly Agent](https://github.com/sml1323/upbit_websocket))에서는 AI로 구현을 가속하되, 아키텍처 설계와 output 검증은 직접 수행하는 방식으로 개선

---

## 주요 기능

### RAG 채팅 - 스트리밍 응답 + 소스 문서 미리보기

<video src="https://github.com/user-attachments/assets/15c993da-600b-4da0-ba38-da105f6b11c7" controls loop muted width="100%"></video>

- 실시간 스트리밍 응답 (SSE)
- 참고 문서 소스 표시, 클릭 시 원문 확인
- Hybrid Search (벡터 유사도 + BM25) + Reranking
- Agentic RAG: Query Rewriting, Self-Correcting Chain

### PARA 대시보드 - 프로젝트 진척도 관리

<video src="https://github.com/user-attachments/assets/d4b8958d-bd06-4c7f-95a9-ce4d8f971b40" controls loop muted width="100%"></video>

- Stale 프로젝트 자동 탐지 (30일 미수정)
- 프로젝트별 진척도 차트

### 임베딩 시각화 - 벡터 공간 탐색

<video src="https://github.com/user-attachments/assets/d4ab599a-0582-48e7-bcc8-4ab532eae8e8" controls loop muted width="100%"></video>

- t-SNE 기반 2D/3D 시각화 (Plotly.js)
- 카테고리별 색상 클러스터링

### 설정 - 모델 & API 관리

<video src="https://github.com/user-attachments/assets/b96d3a6a-4f61-4066-830b-1b54475bd671" controls loop muted width="100%"></video>

- LLM/Embedding 모델 실시간 교체 (OpenAI, Gemini, Ollama)
- 로컬 모델 다운로드 상태 확인

---

## 기술 상세

### Markdown Preprocessor - 헤더 기반 Semantic Chunking

![Markdown Preprocessing Pipeline](docs/images/image.png)

- YAML Frontmatter 추출, 코드 블록 보호, 계층적 헤더 추적
- 적응형 청크 크기 (`min_size` / `max_size` 기반 자동 병합/분할)

> [상세 문서](docs/features/markdown_preprocessor.md)

### LLM Strategy - Protocol 패턴 기반 멀티 모델

![LLM Strategy Protocol](docs/images/LLMStrategy.png)

```python
class LLMStrategy(Protocol):
    def generate(self, messages: List[Message], *, temperature: float = 0.7) -> LLMResponse: ...
    def stream_generate(self, messages: List[Message], ...) -> Iterator[str]: ...
```

| Provider | 구현체 | 특징 |
|----------|--------|------|
| OpenAI | `OpenAILLM` | GPT-4o, GPT-4o-mini |
| Google | `GeminiLLM` | Gemini Pro, Flash |
| Ollama | `OllamaLLM` | 로컬 LLM (Llama, Mistral) |
| Test | `FakeLLM` | API 호출 없는 테스트용 |

> [상세 문서: Folder Scanner](docs/features/folder_scanner.md) | [ChromaDB Store](docs/features/chroma_store.md)

---

## 기술 스택

### Backend

| 카테고리 | 기술 |
|----------|------|
| Language | Python 3.12+ |
| Framework | FastAPI (비동기, 자동 API 문서화) |
| Vector DB | ChromaDB (로컬 SQLite 기반) |
| Metadata DB | SQLite + SQLModel (ORM) |
| Embedding | OpenAI / Sentence Transformers / E5 / Ollama |
| LLM | OpenAI / Gemini / Ollama (Protocol 패턴) |
| Testing | Pytest (Phase별 구조화 테스트) |

### Frontend

| 카테고리 | 기술 |
|----------|------|
| Framework | Next.js 16 + React 19 |
| Styling | Tailwind CSS 4 + shadcn/ui |
| State | React Hooks + SSE Streaming |
| Visualization | Recharts + Plotly.js |

---

## 프로젝트 구조

```
obrag/
├── src/                          # Backend (Python)
│   ├── api/                      # FastAPI 라우터
│   │   ├── main.py               # App Factory, Lifespan
│   │   ├── deps.py               # 의존성 주입 (AppState)
│   │   └── routers/              # 엔드포인트 모듈
│   ├── core/                     # 핵심 비즈니스 로직
│   │   ├── preprocessing/        # Markdown → Chunks
│   │   ├── llm/                  # LLM Strategy (OpenAI, Gemini, Ollama)
│   │   ├── embedding/            # Embedding Strategy (다중 모델)
│   │   ├── rag/                  # RAGChain, Retriever, PromptBuilder
│   │   │   └── agentic/          # Query Rewriting, Self-Correcting
│   │   ├── sync/                 # FolderScanner, IncrementalSyncer
│   │   └── project/              # PARA 프로젝트 Scanner
│   ├── db/                       # ChromaDB + SQLite
│   └── tasktests/                # Phase별 테스트
│
├── front/                        # Frontend (Next.js)
│   ├── app/                      # App Router 페이지
│   ├── components/               # React 컴포넌트 (shadcn/ui)
│   └── lib/                      # API 클라이언트, 타입, 훅
│
├── docker-compose.yml            # 멀티 컨테이너 구성
└── docs/                         # 기술 문서
```

---

## 시작하기

### Docker (권장)

```bash
git clone https://github.com/sml1323/obrag.git
cd obrag

# HOST_VAULT_PATH에 Obsidian Vault 경로 지정
HOST_VAULT_PATH=/path/to/your/vault docker compose up -d
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs

### 로컬 개발

```bash
# 백엔드
uv sync
uvicorn api.main:app --reload --app-dir src

# 프론트엔드
cd front && npm install && npm run dev
```

Settings 페이지에서 Vault 경로, LLM/Embedding 모델, API 키를 설정한 후 Sync를 실행하면 노트가 벡터화됩니다.

---

## 설계 원칙

- **Strategy Pattern**: LLM과 Embedding 모두 Protocol 기반으로 구현체 교체 자유
- **Dependency Injection**: `AppState`를 통한 서비스 주입, 테스트 시 Mock 용이
- **Incremental Sync**: 전체 재처리 대신 변경분만 처리하여 효율성 확보
- **Phase-based Testing**: 기능 단위로 분리된 테스트 구조

---

## 라이선스

이 프로젝트는 개인 포트폴리오 프로젝트입니다.
