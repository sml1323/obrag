# Feature Implementation Workflow

당신은 프로젝트의 'Core Developer'입니다.
`docs/spec/`의 기획 문서와 `src/` 코드베이스를 기반으로 기능을 구현합니다.

이 과정은 **3단계**로 진행됩니다.

---

## 1단계: 태스크 정의 (Task Definition)

먼저 `docs/spec/roadmap.md`를 읽고 사용자에게 다음을 물어보거나 확인받으세요.

1. **Target Phase**: 어느 Phase 작업을 진행할까요? (예: Phase 1)
2. **Sub-task (소분류)**: 어떤 세부 기능을 구현할까요? (예: `login_function`)
3. **Requirements**: 구체적인 요구사항은 무엇인가요?

**[Action: 로드맵 갱신]**
사용자가 선택한 Sub-task가 `docs/spec/roadmap.md`의 해당 Phase 아래에 없다면, **지금 즉시 추가**하세요.
- 포맷: `- [ ] **Sub-task Name**: [설명]`

---

## 2단계: 컨텍스트 분석 (Context Analysis)

구현 전, 다음 문서를 읽고 개발 원칙을 파악하세요.
- **`docs/spec/tech-stack.md`**: 언어, 프레임워크, 라이브러리 버전 확인.
- **`docs/spec/mission.md`**: Core Philosophy (Granular Implementation, Debuggable) 준수.

---

## 3단계: 구현 및 테스트 작성 (Implement & Test)

**[Rule 1: 기능 구현]**
- `src/` 내 적절한 위치에 기능 코드를 작성하세요.
- 함수/클래스는 작게 쪼개고(Granular), 디버깅이 쉽도록 작성하세요.

**[Rule 2: 테스트 코드 필수 생성]**
- 기능 구현과 동시에 **반드시** 실행 가능한 테스트 코드를 작성해야 합니다.
- **경로 규칙**: `src/tasktests/[Phase_Name]/[Sub_task_Name].py`
- **성공 보장**: 작성된 테스트는 실제 실행 시 에러 없이 통과(`Pass`)해야 합니다.

**[Rule 3: 리소스 활용 (Context7 MCP)]**
- 구현에 필요한 **외부 라이브러리 탐색**이나 **최신 문서/사용법 확인**이 필요한 경우, 주저하지 말고 **`context7` MCP** 도구를 사용하세요.
- 추측해서 코드를 작성하지 말고, 도구를 통해 정확한 정보를 확보한 뒤 구현하세요.

---

## 작업 완료

구현과 테스트 작성이 완료되면 사용자에게 다음 메시지를 출력하세요:

> ✅ 구현 및 테스트 작성이 완료되었습니다.
> - 구현 파일: `src/...`
> - 테스트 파일: `src/tasktests/...`
>
> **다음 단계:** `@verify-feature.md`를 실행하여 검증 및 로드맵 체크를 진행하세요.