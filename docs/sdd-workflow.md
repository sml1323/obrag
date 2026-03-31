# AI-Assisted SDD (설계 주도 개발) 워크플로우

이 프로젝트에서 적용한 AI 코딩 워크플로우를 정리한 문서입니다.

AI에게 구현을 위임하되, **설계와 검증은 직접 수행**하는 방식으로 진행했습니다.

---

## 전체 흐름

```
Plan Project → Decompose Task → Plan Subtask → Implement → Verify
     ↑                                                        │
     └──────────────── findings.md에 지식 축적 ←──────────────┘
```

---

## 1. Plan Project — 프로젝트 기획

프로젝트의 방향을 잡는 단계입니다. AI와의 대화를 통해 모호한 아이디어를 구체적인 요구사항으로 정제합니다.

**산출물:**
- `docs/spec/mission.md` — 프로젝트 비전, 개발 철학, 핵심 목표
- `docs/spec/roadmap.md` — Phase별 마일스톤 및 체크리스트
- `docs/spec/tech-stack.md` — 기술 스택 선정 이유

**핵심 원칙:**
- AI가 제안한 구조를 바로 수용하지 않고, "왜 이 선택인가?"를 반복 질문
- Core Value, User Flow, Tech Constraints를 명확히 한 뒤에만 문서 생성

---

## 2. Decompose Task — 태스크 분해

Roadmap의 추상적인 High-Level Task를 구현 가능한 Atomic Sub-task로 분해합니다.

**분해 원칙:**
- **Atomic**: 하나의 커밋으로 완결 가능한 단위
- **Sequential**: 의존성 순서대로 나열
- **Testable**: 각 Sub-task에 대응하는 테스트 작성 가능

**예시:**
```
RAG 파이프라인 구축
  ├── Retriever 클래스 구현 (ChromaDB 검색)
  ├── 프롬프트 템플릿 모듈 구현 (Context 주입)
  └── Generator 연동 (LLM API 호출)
```

---

## 3. Plan Subtask — 서브태스크 상세 계획

각 Sub-task에 대해 구현 전 상세 계획을 수립합니다.

**계획서에 포함되는 항목:**
- 달성 목표
- 기존 코드 패턴 분석 (유사 구현체 참고)
- 생성할 파일 목록 및 역할
- 파일별 코드 설계 (인터페이스, 클래스, 함수 시그니처)
- 검증 계획 (테스트 방법)

---

## 4. Implement — 구현

계획서를 기반으로 AI가 구현합니다.

**규칙:**
- **Granular Implementation**: 함수/클래스는 작게, 디버깅이 쉽도록
- **테스트 필수**: 기능 코드와 함께 `src/tasktests/[Phase]/` 에 테스트 작성
- **2-Action Rule**: 웹 검색이나 파일 조회를 연속 2회 수행하면, 얻은 지식을 즉시 `findings.md`에 기록

---

## 5. Verify — 검증 및 지식 영속화

구현된 기능의 무결성을 검증하고, 휘발성 컨텍스트를 영구 문서로 변환합니다.

**검증 절차:**
1. `pytest` 실행 → 통과 확인
2. `findings.md`에 기술적 의사결정, 트러블슈팅, 외부 지식 기록
3. `roadmap.md` 체크박스 갱신

**3-Strike Rule:** 동일한 방식으로 3번 수정해도 테스트 실패 시, 접근 방식 자체를 변경

---

## 지식 관리: findings.md

프로젝트 전체에서 학습한 내용을 축적하는 파일입니다.

| 카테고리 | 내용 |
|----------|------|
| Decisions | 기술적 의사결정과 그 이유 (예: "왜 ChromaDB인가?") |
| Troubleshooting | 발생한 에러와 해결 방법 |
| Discoveries | 외부 검색으로 알게 된 API 사용법, 라이브러리 팁 |

이 파일을 통해 AI가 이전 세션의 맥락을 잃어도, 프로젝트의 기술적 결정과 교훈을 유지할 수 있었습니다.

---

## 회고: 이 워크플로우에서 배운 것

**효과적이었던 점:**
- Phase별 테스트 구조 덕분에 기능 단위 검증이 용이
- findings.md로 세션 간 지식 유실 방지
- 계획서를 먼저 작성하면 AI의 구현 품질이 크게 향상

**한계:**
- AI가 생성한 코드를 이해하지 못한 채 누적하면 기술 부채가 급격히 증가
