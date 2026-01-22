# Task Decomposition Workflow

당신은 프로젝트의 'Technical Architect'입니다.
`roadmap.md`에 정의된 추상적인 **High-Level Task**를 개발자가 즉시 구현할 수 있는 **Atomic Sub-tasks**로 분해합니다.

이 과정은 **3단계**로 진행됩니다.

---

## 1단계: 타겟 선정 (Target Identification)

1.  `docs/spec/roadmap.md`를 읽고 현재 진행해야 할 **Phase**와 **High-Level Task**를 파악합니다.
2.  사용자에게 어떤 Task를 세분화할지 물어보거나, 진행 상황(`Current Status`)에 맞춰 제안하세요.

    *(예시: "Phase 2의 'RAG 파이프라인' 태스크를 세분화할까요?")*

---

## 2단계: 구조적 분해 (Architectural Breakdown)

선정된 Task를 **구현 가능한 단위**로 쪼개기 위해 다음을 수행하세요.

1.  **컨텍스트 로드**: `docs/spec/tech-stack.md`와 `docs/spec/mission.md`를 읽고 기술 제약 사항을 확인하세요.
2.  **분해 원칙 (Decomposition Rules)**:
    - **Atomic**: 각 Sub-task는 하나의 PR(Pull Request)이나 하나의 커밋으로 끝날 수 있어야 합니다.
    - **Sequential**: 의존성에 따라 순서대로 나열하세요.
    - **Testable**: 각 Sub-task는 `tasktests/` 폴더에 테스트 코드를 작성할 수 있는 단위여야 합니다.

**[생성 예시]**
> Task: "RAG 파이프라인 구축"
> - Sub 1: Retriever 클래스 구현 (ChromaDB 검색)
> - Sub 2: 프롬프트 템플릿 모듈 구현 (Context 주입)
> - Sub 3: Generator 연동 (LLM API 호출)

---

## 3단계: 로드맵 구조조정 (Update Roadmap)

분해한 내용을 `docs/spec/roadmap.md`에 **들여쓰기(Indentation)** 형태로 반영합니다.

**[수정 전]**
```markdown
- [ ] **RAG 파이프라인**: 벡터 검색 + 컨텍스트 주입 + LLM 응답 생성
[수정 후]

Markdown

- [ ] **RAG 파이프라인**: 벡터 검색 + 컨텍스트 주입 + LLM 응답 생성
  - [ ] **Retriever Module**: 쿼리 임베딩 및 ChromaDB Top-k 검색 구현
  - [ ] **Prompt Template**: 검색된 청크를 Context로 주입하는 프롬프트 빌더 구현
  - [ ] **LLM Client**: LLM API(OpenAI/Ollama) 호출 및 응답 처리
주의: 기존의 상위 Task 체크박스는 그대로 두고, 하위 항목을 추가하세요.

작업 완료 선언
로드맵 업데이트가 완료되면 다음을 출력하여 implement-feature.md로 넘어가도록 유도하세요.

✅ Task 분해가 완료되었습니다.

Target: [상위 Task 이름]

Sub-tasks: [N]개 생성됨 (docs/spec/roadmap.md 업데이트 완료)

Next Step: @implement-feature.md를 실행하여 첫 번째 Sub-task부터 구현을 시작하세요.