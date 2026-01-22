# Feature Implementation Workflow

당신은 프로젝트의 'Core Developer'입니다.
`docs/subtask/current_task.md`에 정의된 계획서를 기반으로 기능을 구현합니다.

> **Pre-requisite**: 이 워크플로우를 실행하기 전, `@plan-subtask.md`를 통해 `docs/subtask/current_task.md`가 생성되어 있어야 합니다.

이 과정은 **4단계**로 진행됩니다.

---

## 1단계: 계획서 로드 (Load Task Plan)

1. `docs/subtask/current_task.md`를 읽고 계획 내용을 파악합니다.
2. 계획서에서 다음 정보를 확인합니다:
   - **Target Task**: 구현할 Sub-task 및 Phase
   - **목표**: 달성하려는 핵심 목표
   - **제안하는 구조**: 생성할 파일 목록
   - **파일별 상세 계획**: 코드 설계 (인터페이스, 클래스, 함수)
   - **Verification Plan**: 테스트 방법

> ⚠️ `current_task.md`가 없으면 `@plan-subtask.md`를 먼저 실행하세요.

---

## 2단계: 컨텍스트 확인 (Context Verification)

**"과거의 실수를 반복하지 마세요."**

구현 전, 다음 문서를 읽고 **제약사항**과 **과거의 교훈**을 로드하세요.

1. **`docs/spec/tech-stack.md` & `mission.md`**:
   - 기술 스택 버전과 개발 철학(Granular, Debuggable) 확인.

2. **`docs/spec/findings.md` (중요!)**:
   - **Decisions**: 이전에 결정된 아키텍처나 라이브러리 선택 이유
   - **Troubleshooting**: 관련된 과거 에러 해결 기록
   - **Discoveries**: 활용 가능한 외부 API 팁

> **Check**: `findings.md`에 기록된 "하지 말아야 할 것"이나 "권장 패턴"이 있다면 반드시 준수하세요.

---

## 3단계: 구현 및 테스트 작성 (Implement & Test)

`current_task.md`의 **파일별 상세 계획**을 따라 구현합니다.

**[Rule 1: 기능 구현 (Granular)]**

- `src/` 내 계획서에 명시된 경로에 기능 코드를 작성하세요.
- 함수/클래스는 작게 쪼개고 디버깅이 쉽도록 작성하세요.

**[Rule 2: 테스트 코드 필수 생성]**

- 기능 구현과 동시에 **반드시** 실행 가능한 테스트 코드를 작성해야 합니다.
- **경로 규칙**: `src/tasktests/[Phase]/[Sub_task].py`
- **성공 보장**: 작성된 테스트는 실제 실행 시 에러 없이 통과(`Pass`)해야 합니다.

**[Rule 3: 2-Action Rule (중요!)]**

- **"정보는 휘발됩니다. 파일에 고정하세요."**
- 웹 검색(Search)이나 파일 조회(Read)를 **연속 2회** 수행했다면, 즉시 얻은 지식을 `docs/spec/findings.md`에 요약/기록하세요.

---

## 4단계: 검증 및 완료 (Verify & Complete)

1. pytest로 테스트 실행
2. 성공 시 `docs/spec/roadmap.md`의 체크박스 `[x]` 업데이트

---

## 5단계: 작업 완료 선언

구현과 테스트 파일 작성이 완료되면, **검증 담당자(QA)**에게 넘깁니다.

> ✅ **구현 완료. 검증 단계로 넘어갑니다.**
>
> - 구현 파일: `src/...`
> - 테스트 파일: `src/tasktests/...`
> - 계획서: `docs/subtask/current_task.md`
>
> **Next Step**: `@verify-feature.md`를 실행하여 지식을 저장하세요.
