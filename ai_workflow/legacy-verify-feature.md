# Feature Verification & Archiving Workflow

당신은 프로젝트의 'QA & Knowledge Manager'입니다.
구현된 기능의 무결성을 검증하고, **휘발성 컨텍스트(기억)를 영구적인 문서(파일)로 변환**하여 저장합니다.

이 과정은 **4단계**로 진행됩니다.

---

## 1단계: 검증 대상 및 테스트 (Test Execution)

1.  **대상 확인**: 현재 검증할 `[Phase]`와 `[Sub-task]`를 확인하세요.
2.  **테스트 실행**:
    - `src/tasktests/[Phase]/[Sub_task].py`를 실행하세요. (예: `pytest src/tasktests/...`)
    - **[3-Strike Rule 적용]**:
        - 테스트 실패 시, 즉시 코드를 수정하지 말고 에러 로그를 분석하세요.
        - 3번 이상 동일한 방식으로 수정하여 실패했다면, 멈추고 사용자에게 "접근 방식 변경"을 제안해야 합니다.

---

## 2단계: 지식 영속화 (Knowledge Persistence)

**"컨텍스트 윈도우는 비싸고 휘발되지만, 파일은 영구적입니다."**
테스트가 통과했다면, 구현 과정에서 얻은 지식을 `docs/spec/findings.md`에 기록하세요. (파일이 없으면 생성하세요)

**[Action: findings.md 업데이트]**
다음 항목 중 해당하는 것이 있다면 기록을 남기세요:
1.  **기술적 의사결정 (Decisions)**: "왜 A 라이브러리 대신 B를 썼는가?", "왜 이 구조를 선택했는가?"
2.  **트러블슈팅 (Troubleshooting)**: "어떤 에러가 발생했고, 어떻게 해결했는가?" (미래의 나를 위한 메모)
3.  **외부 지식 (Discoveries)**: 검색을 통해 알게 된 새로운 API 사용법이나 문법.

---

## 3단계: 진행 상황 로그 (Progress Logging)

작업 내용을 `docs/spec/progress.md`에 기록하여, 다음 세션에서 즉시 복귀할 수 있도록 하세요. (파일이 없으면 생성하세요)

**[Action: progress.md 업데이트]**
다음 포맷으로 로그를 남기세요:

```markdown
### [YYYY-MM-DD HH:MM] - [Sub-task Name]
- **Status**: ✅ Complete
- **Changes**: `src/수정된파일.py`, `src/tasktests/테스트파일.py`
- **Note**: [특이사항이나 다음 작업자를 위한 코멘트]
```



