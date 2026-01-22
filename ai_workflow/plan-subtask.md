# Subtask Planning Workflow

당신은 프로젝트의 'Technical Planner'입니다.
`docs/spec/roadmap.md`에서 세분화된 **Sub-task**에 대해 상세 구현 계획을 수립합니다.

이 과정은 **3단계**로 진행됩니다.

---

## 1단계: 타겟 확인 (Target Identification)

1.  `docs/spec/roadmap.md`를 읽고 현재 구현해야 할 **Sub-task**를 파악합니다.
2.  사용자에게 어떤 Sub-task에 대한 계획을 세울지 확인하세요.

    _(예시: "Phase 2의 'LLMStrategy Protocol' 계획을 세울까요?")_

---

## 2단계: 컨텍스트 수집 & 분석 (Context Analysis)

계획 수립 전, 다음을 수행하세요:

### 2-1. 기술 문서 확인

- `docs/spec/tech-stack.md`: 기술 스택 및 아키텍처 제약사항
- `docs/spec/mission.md`: 개발 철학 (Granular, Debuggable, Unit Testing)
- `docs/spec/findings.md`: 관련된 과거 의사결정이나 트러블슈팅

### 2-2. 유사 패턴 탐색

- 기존 `src/`의 유사 구현체를 찾아 **참고할 패턴**을 파악합니다.
- 예: EmbeddingStrategy → LLMStrategy로 확장 시, 기존 `src/core/embedding/` 구조 분석

### 2-3. 필요 시 외부 리서치

- `context7` MCP 서버를 활용하여 라이브러리 문서 조회
- 웹 검색으로 Best Practice 확인

---

## 3단계: 구현 계획서 작성 (Create Plan Document)

수집한 정보를 바탕으로 `docs/subtask/current_task.md`에 계획서를 작성합니다.

**계획서 템플릿:**

```markdown
# [Sub-task 이름] 구현 계획

> **Target Task**: [Phase] - [상위 Task] > [Sub-task 이름]
> **Target Path**: `src/[예정 경로]`

## 목표

[이 Sub-task가 달성하려는 목표 1-2줄 요약]

---

## 기존 패턴 분석

[참고한 기존 코드 구조와 핵심 특징]

---

## 제안하는 구조

[새로 생성할 파일 목록 및 역할]

---

## 파일별 상세 계획

[각 파일에 들어갈 주요 코드 설계 - 인터페이스, 클래스, 함수 시그니처]

---

## Verification Plan

[테스트 방법 및 검증 명령어]

---

## 요약

[생성 파일 수, 테스트 파일, 의존성 등 핵심 정보 표 형태]
```

---

## 4단계: 완료 선언

계획서 작성 후 사용자에게 리뷰를 요청하세요.

> ✅ **계획 수립 완료**
>
> - **Target**: [Sub-task 이름]
> - **계획서**: `docs/subtask/current_task.md`
>
> **Next Step**: 사용자 승인 후 `@implement-feature.md`를 실행하면, `current_task.md`를 읽고 구현을 시작합니다.

---

## 주의사항

- `current_task.md`는 **항상 덮어쓰기**됩니다 (하나의 작업에만 집중).
- 작업 완료 후 `@verify-feature.md` 실행 시 `findings.md`에 핵심 내용이 기록됩니다.
