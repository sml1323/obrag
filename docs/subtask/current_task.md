# [API Integration Tests] 구현 계획

> **Target Task**: Phase 2 - API Integration Tests
> **Target Path**: `src/tasktests/phase2/`

## 목표

- 기존 작성된 API 테스트(`test_api_chat.py`, `test_api_sync.py`)의 커버리지를 점검하고 확실한 통과를 보장합니다.
- Mocking으로 인해 누락된 **App Wiring (Lifespan, Startup, Dependency Injection)** 검증을 위한 새로운 테스트를 추가합니다.
- 전체 API 엔드포인트가 실제 앱 라이프사이클 내에서 정상 작동하는지 확인합니다.

---

## 기존 패턴 분석

- **`test_api_chat.py`**: `sys.modules`를 패치하여 `api.main`의 의존성을 강력하게 격리함. 단위 테스트 성격이 강함.
- **`test_api_sync.py`**: `app.dependency_overrides`를 사용하여 특정 의존성만 교체.
- **`test_api_foundation.py`**: Lifespan을 건너뛰고 기본 라우팅만 테스트.

> **Gap**: 실제 `lifespan`이 실행될 때 `init_app_state`가 정상적으로 호출되고, `Factory`들이 올바르게 연동되어 `AppState`가 구성되는지 검증하는 "Integration" 레벨의 테스트가 부족함.

---

## 제안하는 구조

### 1. `src/tasktests/phase2/test_wiring.py` [NEW]

- `api.main.lifespan`이 정상적으로 실행되는지 검증.
- `init_app_state` 내부에서 `LLMFactory`, `EmbedderFactory`, `ChromaStore` 생성 로직이 호출되는지 확인 (Mocking 활용하되, `sys.modules` 패치 없이).
- 환경변수 설정에 따라 Factory가 적절한 Config를 받는지 검증.

### 2. 기존 테스트 보완 [MODIFY]

- `test_api_chat.py`: 현행 유지 (단위 테스트로써 가치 있음).
- `test_api_sync.py`: 현행 유지.

---

## 파일별 상세 계획

### `src/tasktests/phase2/test_wiring.py`

```python
def test_lifespan_initializes_app_state():
    """
    Lifespan 컨텍스트 진입 시 AppState가 올바르게 초기화되는지 확인.
    LLMFactory.create, EmbedderFactory.create 등을 Mocking하여 호출 여부 및 인자 검증.
    """

def test_app_dependency_injection_chain():
    """
    TestClient(with lifespan)를 사용하여,
    요청 시 get_app_state -> get_chroma_store 등이
    초기화된 상태를 잘 가져오는지 확인.
    """
```

---

## Verification Plan

### Automated Tests

```bash
# 전체 Phase 2 테스트 실행
PYTHONPATH=src pytest src/tasktests/phase2/ -v
```

### Manual Verification

- 테스트 통과 후, 리포트를 통해 커버리지 확인 (Optional).

---

## 요약

| 구분           | 파일명                                  | 역할                                  |
| -------------- | --------------------------------------- | ------------------------------------- |
| **[NEW]**      | `src/tasktests/phase2/test_wiring.py`   | App Startup, Lifespan, DI Wiring 검증 |
| **[Existing]** | `src/tasktests/phase2/test_api_chat.py` | Chat 엔드포인트 상세 로직 검증 (Mock) |
| **[Existing]** | `src/tasktests/phase2/test_api_sync.py` | Sync/Health 엔드포인트 검증           |
