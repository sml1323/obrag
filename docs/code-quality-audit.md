# 코드 품질 감사 보고서 — Obsidian RAG

**감사 범위**: `src/` 프로덕션 코드 전체 (`tasktests/`, `test/` 제외) + `front/` 전체 (`node_modules/`, `.next/` 제외)
**감사 모드**: 리포트 전용 — 파일 수정 없음
**감사 일자**: 2026-03-01

---

## 🔴 심각도: 높음 (HIGH)

### 1. 광범위한 `except Exception` 블록 (13건)

에러를 무시하거나 삼켜버려서 디버깅이 어렵고 장애 원인 추적이 불가능해짐.

| 파일 | 라인 | 내용 | 비고 |
|------|------|------|------|
| `src/db/chroma_store.py` | 392 | `except Exception:` + `pass` | 완전 무시 — 가장 위험 |
| `src/api/routers/chat.py` | 148 | `except Exception as e:` → HTTPException 500 | 에러 타입 구분 없음 |
| `src/api/routers/vault.py` | 187 | `except Exception as e:` | Vault 작업 중 에러 숨김 |
| `src/core/embedding/multilingual_e5_embedder.py` | 90 | `except Exception:` | 모델 로딩 실패 숨김 |
| `src/core/embedding/model_manager.py` | 154 | `except Exception:` | HF 스냅샷 조회 실패 숨김 |
| `src/core/embedding/model_manager.py` | 279 | `except Exception as e:` | 다운로드 실패 숨김 |
| `src/core/embedding/sentence_transformer_embedder.py` | 75 | `except Exception:` | 모델 로딩 실패 숨김 |
| `src/core/sync/folder_scanner.py` | 188 | `except Exception as e:` + print | 파일 스캔 에러를 print로만 처리 |
| `src/core/sync/incremental_syncer.py` | 127 | `except Exception as e:` | 파일 상태 수집 중 에러 |
| `src/core/sync/incremental_syncer.py` | 147 | `except Exception as e:` | 파일 추가 처리 중 에러 |
| `src/core/sync/incremental_syncer.py` | 165 | `except Exception as e:` | 파일 수정 처리 중 에러 |
| `src/core/sync/incremental_syncer.py` | 176 | `except Exception as e:` | 파일 삭제 처리 중 에러 |
| `src/core/rag/agentic/parallel_processor.py` | 48 | `except Exception:` | 병렬 쿼리 에러를 무시함 |

**권장 조치**: 구체적인 예외 타입(`FileNotFoundError`, `ValueError` 등)으로 분리. 모든 예외는 `logging`으로 기록 후 적절히 재발생시킬 것.

---

### 2. `sys.path.insert` 해킹 (3건)

런타임에 Python 경로를 조작하는 패턴. 깨지기 쉽고, 순환 임포트 위험이 있으며, 정적 분석 도구가 작동하지 않음.

| 파일 | 라인 | 내용 |
|------|------|------|
| `src/core/rag/retriever.py` | 12 | `sys.path.insert(0, str(Path(__file__).parent.parent.parent))` |
| `src/core/embedding/factory.py` | 21 | `sys.path.insert(0, str(Path(__file__).parent.parent.parent))` |
| `src/core/llm/factory.py` | 18 | `sys.path.insert(0, str(Path(__file__).parent.parent.parent))` |

**권장 조치**: `PYTHONPATH=src`로 실행하거나, 패키지 구조를 정리하여 명시적 임포트로 전환.

---

### 3. 프로덕션 코드에 `print()` 사용 (4건)

구조화된 로깅이 없음. 내부 정보가 노출될 수 있고, 로그 레벨 구분이 불가능.

| 파일 | 라인 | 내용 | 문제점 |
|------|------|------|--------|
| `src/api/deps.py` | 227 | `print(f"Failed to create dynamic RAGChain: {e}")` | 에러를 print로만 처리 |
| `src/core/sync/folder_scanner.py` | 190 | `print(f"Warning: Failed to process {scanned_file.full_path}: {e}")` | 경고를 print로 출력 |
| `src/core/rag/chain.py` | 41 | `print(response.answer)` | 디버그 코드 잔존 |
| `src/core/rag/retriever.py` | 60 | `print(f"[{chunk.score:.3f}] {chunk.text[:100]}...")` | 내부 점수 + 콘텐츠 노출 |

**권장 조치**: Python `logging` 모듈 도입. `print()` → `logger.warning()` / `logger.error()` / `logger.debug()`로 전환.

---

### 4. 40줄 초과 장함수 (32개)

테스트, 유지보수, 코드 리뷰가 어려움. 상위 10개:

| 파일 | 함수명 | 라인 범위 | 길이 |
|------|--------|-----------|------|
| `src/core/preprocessing/markdown_preprocessor.py` | `semantic_chunk` | 214-348 | **135줄** |
| `src/api/routers/sync.py` | `trigger_sync` | 84-184 | **101줄** |
| `src/api/routers/embedding.py` | `get_collection_vectors` | 173-271 | **99줄** |
| `src/api/routers/para.py` | `list_para_projects` | 52-138 | **87줄** |
| `src/api/deps.py` | `init_app_state` | 50-132 | **83줄** |
| `src/core/sync/incremental_syncer.py` | `sync` | 103-185 | **83줄** |
| `src/core/embedding/model_manager.py` | `download_model` | 211-290 | **80줄** |
| `src/core/project/scanner.py` | `scan_project` | 37-107 | **71줄** |
| `src/core/rag/agentic/hierarchical_chunker.py` | `_chunk_by_size` | 113-173 | **61줄** |
| `src/api/routers/chat.py` | `chat_stream` | 206-266 | **61줄** |

나머지 22개: `generate`, `stream_generate`, `create`, `query`, `query_with_history`, `retrieve`, `_create_parent_chunks`, `_split_to_children`, `self_correcting_chain.query`, `detect_changes`, `scan`, `scan_and_process`, `chroma_store.query`, `create_app`, `_get_dynamic_chain`, `chat`, `get_vault_document`, `get_vault_tree`, `hybrid_search.search`, `embedding/factory.create`, `llm/factory.create`, `folder_scanner.scan_and_process` (각 41~57줄)

**권장 조치**: 큰 함수부터 단일 책임으로 분리. 헬퍼 함수나 서비스 클래스로 추출.

---

### 5. 프론트엔드 `console.error` 남용 (20건 이상)

브라우저 콘솔에 내부 에러가 그대로 노출됨. 사용자 친화적 에러 UI 부재.

| 파일 | 라인 수 | 대표 내용 |
|------|---------|-----------|
| `front/lib/hooks/use-chat.ts` | 7건 (35, 45, 60, 73, 82, 93, 103) | `console.error('Failed to ...', e)` |
| `front/components/settings/settings-form.tsx` | 4건 (79, 130, 154, 177) | `console.error(err)` |
| `front/components/embedding/embedding-scope.tsx` | 2건 (89, 155) | `console.error("Failed to ...", error)` |
| `front/components/para/para-dashboard.tsx` | 2건 (110, 149) | `console.error("Failed to ...", err)` |
| `front/components/embedding/embedding-visualization.tsx` | 1건 (109) | `console.error("Failed to fetch collections:", err)` |
| `front/components/layout/mascot.tsx` | 1건 (54) | `console.error("Failed to load mascot SVG", err)` |
| `front/app/api/chat/route.ts` | 1건 (91) | `console.error("[v0] Chat API error:", error)` |
| `front/lib/hooks/use-sse.ts` | 1건 (79) | `console.error('SSE Error:', err)` |
| `front/components/layout/app-shell.tsx` | 1건 (14) | `.catch(console.error)` |
| `front/components/chat/chat-layout.tsx` | 1건 (14) | `.catch(console.error)` |

**권장 조치**: 로깅 유틸리티 도입 (`dev` 환경에서만 console 출력). 사용자에게는 토스트/알림으로 친화적 메시지 표시.

---

### 6. 빈 catch 블록 (프론트엔드, 1건)

| 파일 | 라인 | 내용 |
|------|------|------|
| `front/lib/hooks/use-sse.ts` | ~71 | `catch { }` — SSE 파싱 에러를 완전히 무시 |

**권장 조치**: 최소한 `console.warn` 또는 fallback 처리 추가.

---

## 🟡 심각도: 보통 (MEDIUM)

### 7. `# type: ignore` 타입 안전성 억제 (5건)

실제 타입 문제를 가리고 있음. 런타임 타입 불일치 위험.

| 파일 | 라인 | 내용 |
|------|------|------|
| `src/api/deps.py` | 81 | `model_name=embedding_model,  # type: ignore` |
| `src/api/deps.py` | 96 | `model_name=embedding_model  # type: ignore` |
| `src/api/deps.py` | 165 | `model_name=model,  # type: ignore` |
| `src/api/routers/sync.py` | 52 | `model_name=model,  # type: ignore` |
| `src/api/routers/embedding.py` | 9 | `from sklearn.manifold import TSNE  # type: ignore[import-untyped]` |

**권장 조치**: 타입 정의를 수정하여 `type: ignore` 없이도 통과하도록 변경. TSNE는 사용하지 않는다면 임포트 자체를 삭제.

---

### 8. 하드코딩된 플레이스홀더 API 키 (2건)

| 파일 | 라인 | 내용 |
|------|------|------|
| `src/core/llm/ollama_llm.py` | 40 | `api_key="ollama"` — 주석: "필수이지만 Ollama에서 무시됨" |
| `src/core/embedding/ollama_embedder.py` | 44-45 | `api_key="ollama"` |

**권장 조치**: 환경 변수 또는 설정 파일에서 읽도록 변경. 코드에 키 값을 직접 넣지 않을 것.

---

### 9. 하드코딩된 localhost URL

#### 백엔드

| 파일 | 내용 |
|------|------|
| `src/api/deps.py` (2곳) | `os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")` |

#### 프론트엔드

| 파일 | 라인 | 내용 |
|------|------|------|
| `front/next.config.ts` | 8 | `destination: 'http://localhost:8000/:path*'` |
| `front/lib/api/client.ts` | 1 | `BACKEND_URL = "http://localhost:8000"` |
| `front/components/settings/settings-form.tsx` | 335, 408 | `placeholder="http://localhost:11434"` |

**권장 조치**: 환경 변수(`NEXT_PUBLIC_BACKEND_URL`, `OLLAMA_BASE_URL`)로 전환. 배포 환경별 설정 분리.

---

### 10. 매직 넘버 (인라인 숫자 리터럴, 5건)

의미가 불분명한 숫자가 코드에 직접 들어가 있음. 변경 시 여러 파일을 수정해야 함.

| 파일 | 라인 | 값 | 권장 상수명 |
|------|------|-----|-------------|
| `src/core/sync/folder_scanner.py` | 154 | `1500` | `DEFAULT_MAX_CHUNK_SIZE` |
| `src/core/sync/incremental_syncer.py` | 81 | `1500` | `DEFAULT_MAX_CHUNK_SIZE` |
| `src/core/rag/agentic/hierarchical_chunker.py` | 30 | `2000` | `DEFAULT_PARENT_CHUNK_SIZE` |
| `src/core/rag/agentic/hierarchical_chunker.py` | 31 | `500` | `DEFAULT_CHILD_CHUNK_SIZE` |

참고: `markdown_preprocessor.py`의 `MAX_CHUNK_SIZE = 1500`은 이미 상수로 정의되어 있어 양호.

**권장 조치**: 모듈 상수 또는 설정 파일로 추출하여 한 곳에서 관리.

---

### 11. 사용 중단된(deprecated) `typing` 임포트 (45개 파일)

Python 3.12+ 기준으로 `List`, `Dict`, `Optional`, `Tuple`, `Union` 등은 내장 타입(`list`, `dict`, `X | None`)으로 대체 가능.

**영향 범위**: `core/llm/`, `core/embedding/`, `core/rag/`, `core/sync/`, `core/domain/`, `config/`, `dtypes/`, `db/`, `api/` — 거의 모든 프로덕션 모듈.

대표 예시:
```python
# 현재 (deprecated)
from typing import Iterator, List, Optional

# 권장 (Python 3.12+)
from collections.abc import Iterator
# List -> list, Optional[X] -> X | None
```

**권장 조치**: 일괄 리팩토링. `ruff` 린터의 `UP` 규칙으로 자동 수정 가능.

---

### 12. 동적 `import_module` 사용 (시작 시점)

| 파일 | 내용 |
|------|------|
| `src/api/main.py` | `engine_module = import_module("db.engine")` |

정적 분석이 불가능하고 순환 임포트 위험이 있음.

**권장 조치**: 가능하면 명시적 `from db.engine import create_db_and_tables`로 전환.

---

## 🟢 심각도: 낮음 (LOW)

### 13. 프론트엔드 `console.log` / `console.warn` (개발 노이즈)

| 파일 | 라인 | 타입 |
|------|------|------|
| `front/app/api/chat/route.ts` | 20, 27, 78 | `console.log` (디버그 트레이스) |
| `front/lib/hooks/use-sse.ts` | 72 | `console.warn` |
| `front/lib/hooks/use-local-storage.ts` | 14, 30 | `console.warn` |

### 14. Docstring에 절대 경로 예시

| 파일 | 라인 | 내용 |
|------|------|------|
| `src/core/sync/folder_scanner.py` | 65 | `FolderScanner("/path/to/obsidian/vault")` — 사용 예시 |

---

## ✅ 문제 없는 항목

| 검사 항목 | 프론트엔드 | 백엔드 |
|-----------|-----------|--------|
| TODO / FIXME / HACK / XXX 주석 | ✅ 없음 | ✅ 없음 |
| `as any` 타입 단언 | ✅ 없음 | 해당 없음 |
| `@ts-ignore` / `@ts-expect-error` | ✅ 없음 | 해당 없음 |
| `eslint-disable` 지시문 | ✅ 없음 | 해당 없음 |
| CORS 와일드카드 `["*"]` | 해당 없음 | ✅ 없음 (localhost:3000 제한) |
| SQL 인젝션 패턴 | 해당 없음 | ✅ 없음 (ORM/파라미터화 사용) |

---

## 📊 요약 통계

| 심각도 | 건수 | 주요 카테고리 |
|--------|------|---------------|
| 🔴 높음 | ~50건+ | 광범위한 except, sys.path 해킹, print 사용, 장함수, 프론트엔드 console.error, 빈 catch |
| 🟡 보통 | ~55건+ | type: ignore, 플레이스홀더 키, 하드코딩 URL, 매직넘버, deprecated typing, 동적 임포트 |
| 🟢 낮음 | ~8건 | console.log/warn, docstring 경로 |

---

## 🎯 권장 수정 우선순위

| 순위 | 작업 | 난이도 | 영향도 |
|------|------|--------|--------|
| 1 | **`logging` 모듈 도입** — 모든 `print()` 교체 | 낮음 | 높음 |
| 2 | **예외 처리 정밀화** — `except Exception` → 구체적 타입 | 중간 | 높음 |
| 3 | **`sys.path` 해킹 제거** — 패키지 구조 정리 | 중간 | 높음 |
| 4 | **설정 중앙화** — 매직넘버를 상수로, URL을 환경변수로 | 낮음 | 중간 |
| 5 | **typing 모던화** — `List` → `list` 등 일괄 변환 | 낮음 | 중간 |
| 6 | **`type: ignore` 해소** — 실제 타입 불일치 수정 | 중간 | 중간 |
| 7 | **프론트엔드 로깅 유틸** — dev 전용 래퍼 도입 | 낮음 | 중간 |
| 8 | **장함수 분할** — `semantic_chunk`(135줄), `trigger_sync`(101줄)부터 | 높음 | 중간 |
