# Tech Stack & Standards

> AI 코딩 에이전트는 이 문서를 **절대적인 기준**으로 삼아 코드를 작성합니다.

---

## Core Stack

| 구분 | 기술 | 비고 |
|------|------|------|
| **Language** | Python 3.10+ | 타입 힌트 필수 사용 |
| **Backend Framework** | FastAPI | 비동기 지원, 자동 API 문서화 |
| **Frontend** | React + Tailwind CSS | Vite 환경 |
| **Vector DB** | ChromaDB | 로컬 SQLite 기반, Docker 지원 |
| **Metadata DB** | SQLite | 진척도, 복습 주기 등 메타데이터 저장 |

---

## AI/ML Stack

| 구분 | 기술 | 비고 |
|------|------|------|
| **Embedding (Local)** | BGE-M3 | 다국어 지원, 로컬 실행 |
| **Embedding (Cloud)** | text-embedding-3-small | OpenAI API |
| **LLM Options** | OpenAI, Gemini, Ollama | 멀티 모델 전환 지원 필수 |
| **LLM Orchestration** | LangChain / LlamaIndex | 선택적 사용 |

---

## Development Tools (Strict Compliance)

| 도구 | 용도 | 규칙 |
|------|------|------|
| **Testing** | Pytest | 모든 핵심 기능은 테스트 코드 동반 필수 |
| **Linting** | Ruff | 코드 품질 검사 |
| **Formatting** | Black | 코드 포맷 통일 |
| **Type Checking** | MyPy | 타입 안정성 확보 |
| **Debugging** | Pdb / VS Code | 디버거 지원 필수 |

---

## Infrastructure & Deployment

| 구분 | 기술 | 비고 |
|------|------|------|
| **Containerization** | Docker, Docker-Compose | 개발/배포 환경 통일 |
| **File Watching** | watchdog (Python) | 옵시디언 폴더 변경 감지 |
| **Desktop App** | Tauri (추후) | Mac App 패키징 시 사용 |

---

## Architecture Constraints

1. **의존성 주입(DI)**: 모든 모듈은 의존성 주입을 통해 테스트 용이성을 확보해야 함.
2. **외부 API Mocking**: LLM, Embedding API 호출은 테스트 시 Mocking 가능해야 함.
3. **증분 처리**: 전체 재처리 대신 변경분만 처리하는 것을 기본으로 함.
4. **설정 분리**: API 키, 모델 선택 등은 환경변수 또는 설정 파일로 분리.

---

## Project Structure (Recommended)

```
obrag/
├── src/
│   ├── api/           # FastAPI 라우터
│   ├── core/          # 핵심 비즈니스 로직
│   │   ├── embedding/ # 임베딩 관련
│   │   ├── llm/       # LLM 연동
│   │   ├── sync/      # 파일 동기화
│   │   └── review/    # 복습 엔진
│   ├── db/            # 데이터베이스 (ChromaDB, SQLite)
│   └── utils/         # 유틸리티 함수
├── frontend/          # React 앱 (별도 디렉토리)
├── tests/             # 테스트 코드
├── docs/              # 문서
│   └── spec/          # 프로젝트 스펙 문서
└── docker/            # Docker 관련 파일
```
