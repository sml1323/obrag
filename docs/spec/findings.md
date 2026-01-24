# Findings & Decisions Log

> 구현 과정에서 얻은 지식과 결정 사항을 기록합니다.

---

## 2026-01-20: 임베딩 모델 통합 (Embedding Model Integration)

### Decisions (기술적 의사결정)

#### 1. Factory 패턴 도입

- **결정**: `EmbedderFactory`를 통해 Config 기반으로 임베더 생성
- **이유**:
  - DI(의존성 주입) 원칙 준수
  - 테스트 시 `FakeEmbedder`로 쉽게 교체 가능
  - 향후 로컬 모델(BGE-M3) 추가 시 Config만 변경하면 됨
- **사용법**:

  ```python
  from core.embedding import EmbedderFactory
  from config.models import OpenAIEmbeddingConfig

  config = OpenAIEmbeddingConfig(model_name="text-embedding-3-small")
  embedder = EmbedderFactory.create(config)
  ```

#### 2. LocalEmbedder Skeleton 전략

- **결정**: 실제 모델 로딩 없이 `NotImplementedError` 반환
- **이유**: Phase 2에서는 OpenAI 우선, 로컬 모델은 추후 구현
- **주의**: `LocalEmbedder.embed()` 호출 시 예외 발생함

---

### Discoveries (외부 지식)

#### ChromaDB EmbeddingFunction 어댑터

- ChromaDB는 자체 `EmbeddingFunction` 인터페이스 사용
- `_EmbeddingFunctionAdapter`로 `EmbeddingStrategy`를 ChromaDB 호환 형태로 변환
- Warning: `DeprecationWarning: legacy embedding function config` 발생 (무시 가능)

---

## 2026-01-20: 증분 동기화 (Incremental Sync)

### Decisions (기술적 의사결정)

#### 1. 변경 감지 방식: mtime + hash 하이브리드

- **결정**: 수정 시간(mtime) 우선 비교 → 다르면 해시 비교
- **이유**:
  - mtime 동일 → 빠른 스킵 (파일 읽기 불필요)
  - mtime 다르고 hash 동일 → `touch`만 된 경우 처리
  - hash가 다를 때만 실제 변경으로 처리
- **참고**: `os.path.getmtime()` 사용

#### 2. Deterministic ID 전략

- **결정**: `{relative_path}::chunk_{index}` 형태
- **이유**: 기존 `{source}_{index}_{content_hash[:8]}` 방식은 내용이 바뀌면 ID도 바뀌어 upsert가 제대로 동작하지 않음
- **주의**: 파일명이 아닌 **relative_path** 사용 (같은 파일명이 다른 폴더에 있을 수 있음)

#### 3. 레지스트리 저장 형식: JSON

- **결정**: SQLite 대신 JSON 파일 사용
- **이유**: Phase 1에서는 간단한 구현 우선, 추후 SQLite로 마이그레이션 가능

---

### Troubleshooting (에러 해결)

#### 1. `SyncRegistry.clear()` shallow copy 버그

- **증상**: `clear()` 호출 후에도 `len(registry) != 0`
- **원인**: `DEFAULT_REGISTRY.copy()`는 shallow copy → 내부 `files` 딕셔너리가 공유됨
- **해결**:

  ```python
  # 수정 전
  self._data = DEFAULT_REGISTRY.copy()

  # 수정 후
  self._data = {"version": REGISTRY_VERSION, "files": {}}
  ```

#### 2. ChromaDB 메타데이터 리스트 에러

- **증상**: `Expected metadata value to be a str, int, float, bool, or None, got list`
- **원인**: YAML frontmatter의 `tags: [test]`가 리스트로 파싱되어 메타데이터에 포함됨
- **해결**: `_normalize_metadata()` 메서드 추가
  ```python
  elif isinstance(value, (list, dict)):
      normalized[key] = json.dumps(value, ensure_ascii=False)
  ```

---

### Discoveries (외부 지식)

#### ChromaDB upsert

- `collection.upsert()`는 ID가 존재하면 update, 없으면 insert
- 존재하지 않는 ID에 대한 `delete()`는 에러 없이 무시됨

---

## 2026-01-23: LLMStrategy Protocol 구현

### Decisions (기술적 의사결정)

#### 1. EmbeddingStrategy 패턴 재사용

- **결정**: `EmbeddingStrategy`와 동일한 구조로 `LLMStrategy` Protocol 설계
- **이유**:
  - 프로젝트 일관성 유지
  - DI(의존성 주입) 원칙 준수
  - `FakeLLM`으로 테스트 용이성 확보
- **파일 구조**:
  ```
  src/core/llm/
  ├── strategy.py      # Protocol + FakeLLM
  ├── openai_llm.py    # OpenAI 구현체
  ├── gemini_llm.py    # Skeleton
  └── ollama_llm.py    # Skeleton
  ```

#### 2. Skeleton 전략 (Gemini, Ollama)

- **결정**: `NotImplementedError` 반환하는 Skeleton만 생성
- **이유**: Phase 2에서는 OpenAI 우선, 나머지는 다음 Sub-task에서 구현
- **주의**: `GeminiLLM.generate()`, `OllamaLLM.generate()` 호출 시 예외 발생

---

### Troubleshooting (에러 해결)

#### 1. OpenAI 클라이언트 초기화 시 API 키 필수

- **증상**: `OpenAILLM()` 인스턴스 생성 시 `OPENAI_API_KEY` 없으면 즉시 예외 발생
- **원인**: `openai.OpenAI()` 생성자가 API 키 없으면 초기화 실패
- **해결**: 테스트에서 API 키 없는 경우 skip 처리
  ```python
  @pytest.fixture
  def llm(self):
      api_key = os.getenv("OPENAI_API_KEY")
      if not api_key:
          pytest.skip("OPENAI_API_KEY not set")
      return OpenAILLM(api_key=api_key)
  ```

---

### Discoveries (외부 지식)

#### OpenAI Chat Completion API 응답 구조

- `response.choices[0].message.content` → 텍스트 응답
- `response.usage.prompt_tokens` → 입력 토큰 수
- `response.usage.completion_tokens` → 출력 토큰 수
- `response.model` → 실제 사용된 모델명 (요청과 다를 수 있음)
