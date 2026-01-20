# Product Roadmap

> **Last Update**: 2026-01-20 10:05
> **Current Status**: Phase 1 완료. 증분 동기화(`IncrementalSyncer`) 구현 및 테스트 통과. 다음은 Phase 2 RAG 채팅 기능.
> **Note**: ChromaDB 메타데이터에 리스트 포함 시 JSON 변환 필요 (`findings.md` 참고)

> 이 로드맵은 프로젝트의 큰 흐름을 정의합니다. 세부 태스크는 각 단계가 진행됨에 따라 동적으로 생성됩니다.

---

## Phase 1: 핵심 기반 마련 (Core Infrastructure)

- [x] **프로젝트 구조 설정**: Python 프로젝트 구조, 의존성 관리(Poetry/pip), 테스트 환경 구축
- [x] **ETL 파이프라인 구축**: Markdown 파싱, YAML 메타데이터 추출, 본문 Chunking 로직 구현
  - [x] **Markdown Preprocessor**: 헤더 기반 Semantic Chunking, YAML frontmatter 추출, 코드 블록 보호
  - [x] **Folder Scanner**: 폴더 재귀 탐색, 파일 메타데이터(폴더 경로, 파일명) 추출
- [x] **Vector DB 연동**: ChromaDB 설정 및 임베딩 저장/조회 기능 구현
- [x] **증분 동기화(Sync)**: 파일 해시/수정시간 비교 기반 변경 파일만 업데이트하는 로직

---

## Phase 2: RAG 채팅 기능 (Intelligent Chat)

- [ ] **임베딩 모델 통합**: BGE-M3(로컬) / text-embedding-3-small(클라우드) 선택 가능
- [ ] **멀티 LLM 지원**: OpenAI, Gemini, Ollama 연동 및 전환 기능
- [ ] **RAG 파이프라인**: 벡터 검색 + 컨텍스트 주입 + LLM 응답 생성
- [ ] **FastAPI 백엔드**: REST API 엔드포인트 구현

---

## Phase 3: PARA 대시보드 (Project Dashboard)

- [ ] **프로젝트 스캐닝**: `Project/` 폴더 하위 디렉토리 자동 인식
- [ ] **메타데이터 관리**: SQLite 기반 진척도, 최종 활동일 저장
- [ ] **유기 프로젝트 감지**: 30일 이상 수정 없는 프로젝트 경고 표시
- [ ] **Frontend UI**: React + Tailwind 기반 대시보드 구현

---

## Phase 4: 에빙하우스 복습 엔진 (Memory Boost)

- [ ] **태그 기반 관리**: `#review` 태그 노트 추적 시스템
- [ ] **복습 주기 계산**: 에빙하우스 주기(1, 3, 7, 14, 30일) 기반 알림 로직
- [ ] **YAML 메타데이터 업데이트**: `last_review_date`, `review_count` 자동 관리
- [ ] **랜덤 복습 기능**: 전체 지식 가볍게 훑기 버튼

---

## Phase 5: 통합 및 완성 (Integration & Polish)

- [ ] **End-to-End Flow 검증**: 핵심 사용 시나리오 전체 테스트
- [ ] **Docker 컨테이너화**: Docker-Compose 기반 환경 구성
- [ ] **Refinement & Refactoring**: 학습 기반 구조 개선
- [ ] **Desktop App 패키징**: Tauri 기반 Mac App 전환 (Optional)
