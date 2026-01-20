# Findings & Decisions Log

> 구현 과정에서 얻은 지식과 결정 사항을 기록합니다.

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
