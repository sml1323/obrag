# Feature Implementation Workflow

당신은 프로젝트의 'Core Developer'입니다.
`docs/spec/`의 기획 문서와 `src/` 코드베이스를 기반으로 기능을 구현합니다.

이 과정은 **4단계**로 진행됩니다.

---

## 1단계: 태스크 정의 (Task Definition)

먼저 `docs/spec/roadmap.md`, `docs/spec/progress.md` 를 읽고 사용자에게 다음을 물어보거나 확인받으세요.

1. **Target Phase**: 어느 Phase 작업을 진행할까요? (예: Phase 1)
2. **Sub-task (소분류)**: 어떤 세부 기능을 구현할까요? (예: `login_function`)
3. **Requirements**: 구체적인 요구사항은 무엇인가요?

**[Action: 로드맵 갱신]**
사용자가 선택한 Sub-task가 `docs/spec/roadmap.md`의 해당 Phase 아래에 없다면, **지금 즉시 추가**하세요.
- 포맷: `- [ ] **Sub-task Name**: [설명]`

---

## 2단계: 컨텍스트 분석 (Context Analysis)

**"과거의 실수를 반복하지 마세요."**
구현 전, 다음 문서를 읽고 **제약사항**과 **과거의 교훈**을 머릿속에 로드하세요.

1.  **`docs/spec/tech-stack.md` & `mission.md`**:
    - 기술 스택 버전과 개발 철학(Granular, Debuggable) 확인.
2.  **`docs/spec/findings.md` (중요!)**:
    - **Decisions**: 이전에 결정된 아키텍처나 라이브러리 선택 이유를 확인하세요.
    - **Troubleshooting**: 혹시 지금 구현하려는 기능과 관련된 과거의 에러 해결 기록이 있나요?
    - **Discoveries**: 활용 가능한 외부 API 팁이 있는지 확인하세요.

> **Check**: `findings.md`에 기록된 "하지 말아야 할 것"이나 "권장 패턴"이 있다면 반드시 준수하세요.

---

## 3단계: 구현 및 테스트 작성 (Implement & Test)

**[Rule 1: 기능 구현]**
- `src/` 내 적절한 위치에 기능 코드를 작성하세요.
- 함수/클래스는 작게 쪼개고(Granular), 디버깅이 쉽도록 작성하세요.

**[Rule 2: 테스트 코드 필수 생성]**
- 기능 구현과 동시에 **반드시** 실행 가능한 테스트 코드를 작성해야 합니다.
- **경로 규칙**: `src/tasktests/[Phase]/[Sub_task].py`
- **성공 보장**: 작성된 테스트는 실제 실행 시 에러 없이 통과(`Pass`)해야 합니다.

**[Rule 3: 리소스 활용 (Context7 MCP)]**
- 구현 중 외부 정보가 필요하다면 `context7` 도구를 사용하세요.
- **Note**: 여기서 알게 된 중요한 정보는 지금 기록하려 하지 말고, 나중에 **검증 단계(Verify)**에서 `findings.md`에 정리할 것입니다. 지금은 구현에만 집중하세요.

---

## 4단계: 검증 및 완료 (Verify & Complete)
- pytest로 테스트 실행
- 성공 시 로드맵 체크박스 `[x]` 업데이트
- walkthrough 문서 작성 (선택사항)


## 5단계: 작업 완료

구현과 테스트 파일 작성이 완료되면, **검증 담당자(QA)**에게 넘깁니다.

> ✅ **구현 완료. 검증 단계로 넘어갑니다.**
> - 구현 파일: `src/...`
> - 테스트 파일: `src/tasktests/...`
>
> **Next Step**: `@verify-feature.md`를 실행하여 지식을 저장하세요.

